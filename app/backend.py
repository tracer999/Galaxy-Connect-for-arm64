# PowerShell 스크립트를 실행하고 결과를 화면에 넘긴다.
# 실제 동작 로직은 저장소 루트의 *.ps1 에만 있고, 여기서는 호출과 결과 전달만 한다.
import base64
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

APP_NAME = 'Galaxy Connect for ARM64'
VERSION = '1.0.0'

POWERSHELL = str(Path(os.environ.get('WINDIR', r'C:\Windows')) / 'System32' / 'WindowsPowerShell' / 'v1.0' / 'powershell.exe')
ACTIONS = {'apply': 'Apply.ps1', 'backup': 'Backup.ps1', 'restore': 'Restore.ps1'}
NO_WINDOW = subprocess.CREATE_NO_WINDOW

# 묶은 exe 는 풀린 임시 폴더의 scripts, 개발 중에는 저장소 루트의 스크립트를 쓴다
SCRIPTS_DIR = Path(sys._MEIPASS) / 'scripts' if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent.parent
# exe 는 실행할 때마다 임시 폴더에 풀리므로 설정과 백업은 사용자 데이터 폴더에 둔다
DATA_DIR = Path(os.environ['APPDATA']) / APP_NAME
SETTINGS_PATH = DATA_DIR / 'settings.json'


def read_settings():
    try:
        return json.loads(SETTINGS_PATH.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def write_settings(patch):
    settings = {**read_settings(), **patch}
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding='utf-8')
    return settings


def ps_quote(s):
    return "'" + str(s).replace("'", "''") + "'"


def encode(cmd):
    return base64.b64encode(cmd.encode('utf-16-le')).decode('ascii')


# lib\Common.ps1 이 이 환경 변수를 읽어 백업 위치로 쓴다
def backup_env():
    return f"$env:GC_ARM64_BACKUP_DIR={ps_quote(DATA_DIR / 'backup')};"


def powershell(cmd):
    return [POWERSHELL, '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-EncodedCommand', encode(cmd)]


# 관리자 권한 없이 Status.ps1 -Json 을 실행해 상태를 읽는다
def get_status():
    cmd = f"[Console]::OutputEncoding=[Text.Encoding]::UTF8; {backup_env()} & {ps_quote(SCRIPTS_DIR / 'Status.ps1')} -Json -LogLines 8"
    r = subprocess.run(powershell(cmd), capture_output=True, creationflags=NO_WINDOW)
    stdout = r.stdout.decode('utf-8', 'replace')
    line = next((l for l in reversed(stdout.splitlines()) if l.strip().startswith('{')), None)
    if not line:
        raise RuntimeError((r.stderr.decode('mbcs', 'replace') or 'No output from Status.ps1').strip())
    return json.loads(line)


# 관리자 권한(UAC)으로 스크립트를 실행하고, 출력 파일을 읽어 줄 단위로 on_line 에 넘긴다
def run_action(name, on_line):
    script = ACTIONS[name]
    log_file = Path(tempfile.gettempdir()) / f'gc-arm64-{name}-{int(time.time() * 1000)}.log'
    # 관리자 권한으로 새로 뜨는 프로세스 안에서 환경 변수를 설정해야 확실히 전달된다
    inner = (f"{backup_env()} & {{ try {{ & {ps_quote(SCRIPTS_DIR / script)} }} catch {{ Write-Host ('ERROR: ' + $_.Exception.Message) }} }}"
             f" *>&1 | Out-File -Encoding utf8 -FilePath {ps_quote(log_file)}")
    outer = (f"$p = Start-Process -FilePath {ps_quote(POWERSHELL)} -Verb RunAs -WindowStyle Hidden -Wait -PassThru"
             f" -ArgumentList '-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-EncodedCommand','{encode(inner)}'"
             " ; exit $p.ExitCode")

    sent = 0

    def pump(final=False):
        nonlocal sent
        try:
            lines = log_file.read_text(encoding='utf-8-sig').splitlines()
        except OSError:
            return
        # 쓰는 중인 마지막 줄은 다음 번에 보낸다 (끝났으면 남은 줄을 모두 보낸다)
        complete = lines[sent:] if final else lines[sent:-1]
        for l in complete:
            if l.strip():
                on_line(l)
        sent += len(complete)

    proc = subprocess.Popen(powershell(outer), stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, creationflags=NO_WINDOW)
    while proc.poll() is None:
        time.sleep(0.4)
        pump()
    stderr = proc.stderr.read().decode('mbcs', 'replace')
    pump(final=True)
    try:
        log_file.unlink()
    except OSError:
        pass  # 로그 파일이 없으면 UAC 가 취소된 것
    cancelled = 'cancel' in stderr.lower() or '취소' in stderr
    return {'ok': proc.returncode == 0 and not cancelled, 'cancelled': cancelled, 'code': proc.returncode, 'error': stderr.strip() or None}
