import React, { useCallback, useEffect, useRef, useState } from 'react';
import { STRINGS, LANGS, defaultLang } from './i18n.js';

const api = window.api;

const Icon = {
  link: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M9 17H7A5 5 0 0 1 7 7h2m6 0h2a5 5 0 0 1 0 10h-2m-7-5h8" stroke="#2563EB" strokeWidth="2.2" strokeLinecap="round" /></svg>
  ),
  check: () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M20 6 9 17l-5-5" stroke="#12B76A" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" /></svg>
  ),
  warning: ({ size = 24 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none"><path d="M12 9v4m0 4h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" stroke="#DC6803" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
  ),
  play: () => (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none"><path d="M7 5v14l11-7L7 5Z" stroke="#2563EB" strokeWidth="2" strokeLinejoin="round" /></svg>
  ),
};

const isSamsung = v => /samsung/i.test(v || '');

// Galaxy Connect 로그 한 줄을 "HH:MM:SS  메시지" 로 줄인다
// 원본 형식: "2026-10-17 12:18:49.9426 [INFO] [P:.. | T:..] [File.cs::Method (56)] \t메시지"
function shortLog(line) {
  const time = line.match(/^\S+ (\d\d:\d\d:\d\d)/)?.[1];
  const message = line.includes('\t') ? line.slice(line.lastIndexOf('\t') + 1) : line.replace(/^.*\]\s+/, '');
  return time ? `${time}  ${message.trim().slice(0, 120)}` : line;
}

function heroState(status, error) {
  if (error) return 'error';
  if (!status) return null;
  if (!status.GalaxyConnect) return 'notInstalled';
  if (status.Detection?.IsSamsungDevice) return 'ready';
  if (isSamsung(status.AppSees?.Manufacturer)) return 'launch';
  return 'notApplied';
}

function Button({ type = 'secondary', busy, grow, children, ...rest }) {
  return (
    <button className={`btn ${type}${grow ? ' grow' : ''}`} {...rest}>
      {busy && <span className="spinner" />}
      {children}
    </button>
  );
}

const Badge = ({ tone, children }) => <span className={`badge ${tone}`}>{children}</span>;

const InfoRow = ({ label, value }) => (
  <div className="row"><span className="label">{label}</span><span className="value">{value}</span></div>
);

function Modal({ wide, children }) {
  return <div className="scrim" role="dialog" aria-modal="true"><div className={`dialog${wide ? ' wide' : ''}`}>{children}</div></div>;
}

function ConsentDialog({ s, onAccept, onQuit }) {
  const [agreed, setAgreed] = useState(false);
  return (
    <Modal>
      <div className="ring warning" style={{ width: 44, height: 44 }}><Icon.warning /></div>
      <h2>{s.consent.title}</h2>
      <ul className="points">
        {s.consent.points.map((p, i) => <li key={i} className={i === 1 ? 'key' : ''}>{p}</li>)}
      </ul>
      <label className="agree">
        <input type="checkbox" checked={agreed} onChange={e => setAgreed(e.target.checked)} />
        {s.consent.agree}
      </label>
      <div className="dialog-actions">
        <Button onClick={onQuit}>{s.consent.quit}</Button>
        <Button type="primary" disabled={!agreed} onClick={onAccept}>{s.consent.start}</Button>
      </div>
    </Modal>
  );
}

function LogDialog({ s, lines, onClose }) {
  return (
    <Modal wide>
      <h2>{s.log}</h2>
      <pre className="log">{lines.length ? lines.join('\n') : s.logEmpty}</pre>
      <div className="dialog-actions">
        <Button onClick={onClose}>{s.close}</Button>
      </div>
    </Modal>
  );
}

function ConfirmDialog({ s, action, onCancel, onOk }) {
  const c = s.confirm[action];
  return (
    <Modal>
      <h2>{c.title}</h2>
      <p className="muted" style={{ fontSize: 14 }}>{c.body}</p>
      <div className="dialog-actions">
        <Button onClick={onCancel}>{s.confirm.cancel}</Button>
        <Button type={action === 'restore' ? 'danger' : 'primary'} onClick={onOk}>{s.confirm.ok}</Button>
      </div>
    </Modal>
  );
}

export default function App() {
  const [settings, setSettings] = useState(null);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [checkedAt, setCheckedAt] = useState(null);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(null);
  const [confirm, setConfirm] = useState(null);
  const [actionLog, setActionLog] = useState([]);
  const [result, setResult] = useState(null);
  const [showLog, setShowLog] = useState(false);
  // 작업이 끝났을 때 ERROR 줄이 있었는지 보려고 화면 상태와 별도로 들고 있는다
  const actionLogRef = useRef([]);

  const lang = settings?.lang || defaultLang();
  const s = STRINGS[lang];

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      setStatus(await api.getStatus());
      setError(null);
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setCheckedAt(new Date());
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    api.getSettings().then(setSettings);
    refresh();
    return api.onActionLog(line => {
      actionLogRef.current = [...actionLogRef.current, line];
      setActionLog(actionLogRef.current);
    });
  }, [refresh]);

  const updateSettings = async patch => setSettings(await api.setSettings(patch));

  async function run(action) {
    setConfirm(null);
    setBusy(action);
    setResult(null);
    actionLogRef.current = [];
    setActionLog([]);
    const r = await api.runAction(action);
    setBusy(null);
    const failed = !r.ok || actionLogRef.current.some(l => l.startsWith('ERROR'));
    setResult(r.cancelled ? 'cancelled' : failed ? 'failed' : 'ok');
    refresh();
  }

  const state = heroState(status, error);
  const st = state && s.states[state];
  const time = checkedAt?.toLocaleTimeString(lang === 'ko' ? 'ko-KR' : 'en-US', { hour: 'numeric', minute: '2-digit' });
  const logLines = actionLog.length ? actionLog : (status?.Log || []).map(shortLog);

  return (
    <div className="window">
      <header className="header">
        <div className="logo"><Icon.link /></div>
        <div className="titles">
          <h1>Galaxy Connect for ARM64</h1>
          <p>{s.subtitle}</p>
        </div>
        <div className="segment" role="group" aria-label="Language">
          {LANGS.map(([code, label]) => (
            <button key={code} aria-pressed={code === lang} onClick={() => updateSettings({ lang: code })}>{label}</button>
          ))}
        </div>
      </header>

      <main className="body">
        <section className="card hero">
          {!st ? (
            <p className="muted">{s.loading}</p>
          ) : (
            <>
              <div className={`ring ${state === 'ready' ? 'success' : state === 'launch' ? 'primary' : 'warning'}`}>
                {state === 'ready' ? <Icon.check /> : state === 'launch' ? <Icon.play /> : <Icon.warning />}
              </div>
              <div className="hero-text">
                <h2>{st.title}</h2>
                <p className="desc">{state === 'error' ? error : st.body}</p>
              </div>
              {time && <p className="small">{s.lastChecked(time)}</p>}
            </>
          )}
        </section>

        <div className="cards">
          <section className="card status">
            <div className="card-head">
              <h2>{s.status}</h2>
              <Button disabled={loading || !!busy} busy={loading} onClick={refresh}>{s.refresh}</Button>
            </div>
            {status && (
              <>
                <InfoRow label={s.rows.detection} value={
                  !status.Detection ? <Badge tone="neutral">{s.none}</Badge>
                    : status.Detection.IsSamsungDevice ? <Badge tone="success">{s.badgeDetected}</Badge>
                    : <Badge tone="warning">{s.badgeNotDetected}</Badge>
                } />
                <InfoRow label={s.rows.gc} value={status.GalaxyConnect || s.notInstalled} />
                <InfoRow label={s.rows.mc} value={status.MultiControl || s.notInstalled} />
                <InfoRow label={s.rows.service} value={s.service[status.Service] || status.Service || s.none} />
              </>
            )}
          </section>

          <section className="card">
            <div className="card-head">
              <h2>{s.actions}</h2>
              <Button onClick={() => setShowLog(true)}>{s.viewLog}</Button>
            </div>
            <p className="muted">{s.actionsBody}</p>
            <div className="buttons">
              <Button type="primary" grow disabled={!!busy} busy={busy === 'apply'} onClick={() => setConfirm('apply')}>
                {busy === 'apply' ? s.running : s.apply}
              </Button>
              <Button disabled={!!busy} busy={busy === 'backup'} onClick={() => run('backup')}>{s.backup}</Button>
              <Button type="danger" disabled={!!busy} busy={busy === 'restore'} onClick={() => setConfirm('restore')}>{s.restore}</Button>
            </div>
            <div className="note"><Icon.warning size={16} /><span>{s.note}</span></div>
            {result && <div className={`toast ${result === 'ok' ? 'ok' : 'fail'}`}>{s.done[result]}</div>}
          </section>
        </div>
      </main>

      <footer className="footer">
        <span>{s.footer}</span>
        <span>v1.0.0</span>
      </footer>

      {settings && !settings.consented && (
        <ConsentDialog s={s} onAccept={() => updateSettings({ consented: true, consentedAt: new Date().toISOString() })} onQuit={() => api.quit()} />
      )}
      {showLog && <LogDialog s={s} lines={logLines} onClose={() => setShowLog(false)} />}
      {confirm && <ConfirmDialog s={s} action={confirm} onCancel={() => setConfirm(null)} onOk={() => run(confirm)} />}
    </div>
  );
}
