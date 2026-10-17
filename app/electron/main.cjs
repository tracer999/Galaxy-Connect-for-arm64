// Electron 메인 프로세스: 창을 띄우고 PowerShell 스크립트를 실행한다.
// 실제 동작 로직은 저장소 루트의 *.ps1 에만 있고, 여기서는 호출과 결과 전달만 한다.
const { app, BrowserWindow, ipcMain, shell } = require('electron');
const { execFile, spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const POWERSHELL = path.join(process.env.WINDIR || 'C:\\Windows', 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe');
const ACTIONS = { apply: 'Apply.ps1', backup: 'Backup.ps1', restore: 'Restore.ps1' };

// 패키징된 앱은 resources\scripts, 개발 중에는 저장소 루트의 스크립트를 쓴다
const scriptsDir = app.isPackaged
  ? path.join(process.resourcesPath, 'scripts')
  : path.resolve(__dirname, '..', '..');

const settingsPath = () => path.join(app.getPath('userData'), 'settings.json');

function readSettings() {
  try { return JSON.parse(fs.readFileSync(settingsPath(), 'utf8')); } catch { return {}; }
}

function writeSettings(patch) {
  const next = { ...readSettings(), ...patch };
  fs.mkdirSync(path.dirname(settingsPath()), { recursive: true });
  fs.writeFileSync(settingsPath(), JSON.stringify(next, null, 2));
  return next;
}

const psQuote = s => `'${String(s).replace(/'/g, "''")}'`;
const encode = cmd => Buffer.from(cmd, 'utf16le').toString('base64');
// 백업은 앱을 닫아도 남도록 사용자 데이터 폴더에 둔다 (lib\Common.ps1 이 이 환경 변수를 읽는다)
const backupEnv = () => `$env:GC_ARM64_BACKUP_DIR=${psQuote(path.join(app.getPath('userData'), 'backup'))};`;

// 관리자 권한 없이 Status.ps1 -Json 을 실행해 상태를 읽는다
function getStatus() {
  const cmd = `[Console]::OutputEncoding=[Text.Encoding]::UTF8; ${backupEnv()} & ${psQuote(path.join(scriptsDir, 'Status.ps1'))} -Json -LogLines 8`;
  return new Promise((resolve, reject) => {
    execFile(POWERSHELL, ['-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-EncodedCommand', encode(cmd)],
      { windowsHide: true, encoding: 'utf8', maxBuffer: 4 * 1024 * 1024 },
      (err, stdout, stderr) => {
        const line = stdout.split(/\r?\n/).reverse().find(l => l.trim().startsWith('{'));
        if (!line) return reject(new Error((stderr || err?.message || 'No output from Status.ps1').trim()));
        try { resolve(JSON.parse(line)); } catch (e) { reject(e); }
      });
  });
}

// 관리자 권한(UAC)으로 스크립트를 실행하고, 출력 파일을 읽어 줄 단위로 화면에 보낸다
function runAction(win, name) {
  const script = ACTIONS[name];
  if (!script) return Promise.reject(new Error(`Unknown action: ${name}`));
  const logFile = path.join(os.tmpdir(), `gc-arm64-${name}-${Date.now()}.log`);
  // 관리자 권한으로 새로 뜨는 프로세스 안에서 환경 변수를 설정해야 확실히 전달된다
  const inner = `${backupEnv()} & { try { & ${psQuote(path.join(scriptsDir, script))} } catch { Write-Host ('ERROR: ' + $_.Exception.Message) } } *>&1 | Out-File -Encoding utf8 -FilePath ${psQuote(logFile)}`;
  const outer = [
    `$p = Start-Process -FilePath ${psQuote(POWERSHELL)} -Verb RunAs -WindowStyle Hidden -Wait -PassThru`,
    `-ArgumentList '-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-EncodedCommand','${encode(inner)}'`,
    '; exit $p.ExitCode',
  ].join(' ');

  return new Promise(resolve => {
    let sent = 0;
    const pump = () => {
      let text = '';
      try { text = fs.readFileSync(logFile, 'utf8').replace(/^\uFEFF/, ''); } catch { return; }
      const lines = text.split(/\r?\n/);
      const complete = lines.slice(sent, lines.length - 1);
      for (const l of complete) if (l.trim()) win.webContents.send('action-log', l);
      sent += complete.length;
    };
    const timer = setInterval(pump, 400);
    let stderr = '';
    const child = spawn(POWERSHELL, ['-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-EncodedCommand', encode(outer)], { windowsHide: true });
    child.stderr.on('data', d => { stderr += d.toString('utf8'); });
    child.on('close', code => {
      clearInterval(timer);
      pump();
      // 마지막 줄에 줄바꿈이 없을 수 있으니 남은 내용도 보낸다
      try {
        const rest = fs.readFileSync(logFile, 'utf8').replace(/^\uFEFF/, '').split(/\r?\n/).slice(sent).filter(l => l.trim());
        for (const l of rest) win.webContents.send('action-log', l);
        fs.unlinkSync(logFile);
      } catch { /* 로그 파일이 없으면 UAC 가 취소된 것 */ }
      const cancelled = /cancel|취소/i.test(stderr);
      resolve({ ok: code === 0 && !cancelled, cancelled, code, error: stderr.trim() || null });
    });
  });
}

function createWindow() {
  const win = new BrowserWindow({
    // Figma "Compact · KO/EN" 프레임과 같은 크기 (제목 표시줄 제외한 내용 영역 기준)
    width: 780,
    height: 600,
    minWidth: 780,
    minHeight: 600,
    useContentSize: true,
    backgroundColor: '#F5F6F8',
    autoHideMenuBar: true,
    title: 'Galaxy Connect for ARM64',
    webPreferences: { preload: path.join(__dirname, 'preload.cjs'), contextIsolation: true, nodeIntegration: false, sandbox: true },
  });
  win.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
  // 외부 링크는 기본 브라우저로 연다
  win.webContents.setWindowOpenHandler(({ url }) => { shell.openExternal(url); return { action: 'deny' }; });

  ipcMain.handle('get-status', () => getStatus());
  ipcMain.handle('run-action', (_e, name) => runAction(win, name));
  ipcMain.handle('get-settings', () => readSettings());
  ipcMain.handle('set-settings', (_e, patch) => writeSettings(patch));
  ipcMain.handle('quit', () => app.quit());
}

app.whenReady().then(createWindow);
app.on('window-all-closed', () => app.quit());
