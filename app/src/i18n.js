// 화면 문자열. 새 언어를 추가하려면 같은 키로 객체를 하나 더 만든다.
export const STRINGS = {
  ko: {
    subtitle: 'ARM64 · Snapdragon PC용 비공식 도구',
    loading: '상태를 확인하는 중…',
    states: {
      ready: { title: '준비 완료', body: 'Galaxy Connect가 이 PC를 지원 기기로 인식하고 있습니다. Multi Control을 바로 사용할 수 있습니다.' },
      launch: { title: '적용됨 · 앱 실행 필요', body: '레지스트리가 적용되었습니다. Galaxy Connect를 실행하고 Samsung 계정으로 로그인하면 판정이 끝납니다.' },
      notApplied: { title: '아직 적용되지 않음', body: 'Galaxy Connect가 이 PC를 지원하지 않는 기기로 보고 있습니다. "적용하기"를 눌러 주세요.' },
      notInstalled: { title: 'Galaxy Connect 미설치', body: 'Microsoft Store에서 Galaxy Connect와 Multi Control을 먼저 설치한 뒤 "적용하기"를 눌러 주세요.' },
      error: { title: '상태를 읽지 못했습니다', body: '' },
    },
    badgeDetected: '삼성 PC로 인식',
    badgeNotDetected: '인식 안 됨',
    lastChecked: t => `마지막 확인: ${t}`,
    actions: '작업',
    actionsBody: '적용하면 Galaxy Connect가 기기를 다시 판정합니다.',
    apply: '적용하기', backup: '백업', restore: '복원', running: '실행 중…',
    note: '적용·복원 시 Galaxy Connect 앱 데이터가 초기화되어 Samsung 계정에 다시 로그인해야 합니다.',
    status: '상태', refresh: '새로고침', viewLog: '로그 보기', close: '닫기',
    rows: { detection: 'Galaxy Connect 인식', gc: 'Galaxy Connect 버전', mc: 'Multi Control 버전', service: '서비스' },
    notInstalled: '미설치', none: '없음',
    service: { Running: '실행 중', Stopped: '중지됨' },
    log: '실행 로그', logEmpty: '아직 기록이 없습니다.',
    footer: '비공식 도구 · Samsung과 관계없음 · 사용 책임은 실행한 본인에게 있습니다',
    done: { ok: '완료했습니다.', cancelled: '관리자 권한 요청이 취소되었습니다.', failed: '오류가 발생했습니다. 로그를 확인하세요.' },
    consent: {
      title: '사용 전에 확인해 주세요',
      points: [
        '이 프로그램은 레지스트리의 제조사 값을 바꿔 Galaxy Connect가 이 PC를 삼성 PC로 인식하게 합니다.',
        '실행해서 생기는 모든 결과의 책임은 직접 실행한 본인에게 있습니다. 작성자는 어떤 손해에도 책임지지 않습니다.',
        'Samsung 서비스 약관에 맞지 않을 수 있으며, 계정 이용에 불이익이 생길 수 있습니다.',
      ],
      agree: '위 내용을 이해했으며 동의합니다', quit: '종료', start: '동의하고 시작',
    },
    confirm: {
      apply: { title: '적용할까요?', body: 'Galaxy Connect 앱 데이터가 초기화됩니다. 적용한 뒤 Galaxy Connect를 실행해 Samsung 계정으로 다시 로그인하세요.' },
      restore: { title: '원래대로 복원할까요?', body: '레지스트리를 원래 값으로 되돌리고 Galaxy Connect 앱 데이터를 초기화합니다. 이후 Galaxy Connect와 Multi Control은 이 PC에서 동작하지 않습니다.' },
      cancel: '취소', ok: '계속',
    },
  },
  en: {
    subtitle: 'Unofficial tool for ARM64 · Snapdragon PCs',
    loading: 'Checking status…',
    states: {
      ready: { title: 'Ready', body: 'Galaxy Connect recognizes this PC as a supported device. Multi Control is ready to use.' },
      launch: { title: 'Applied · launch the app', body: 'The registry is applied. Launch Galaxy Connect and sign in to your Samsung account to finish detection.' },
      notApplied: { title: 'Not applied yet', body: 'Galaxy Connect treats this PC as unsupported. Click "Apply" to continue.' },
      notInstalled: { title: 'Galaxy Connect not installed', body: 'Install Galaxy Connect and Multi Control from the Microsoft Store first, then click "Apply".' },
      error: { title: 'Could not read status', body: '' },
    },
    badgeDetected: 'Samsung PC',
    badgeNotDetected: 'Not detected',
    lastChecked: t => `Last checked: ${t}`,
    actions: 'Actions',
    actionsBody: 'Applying makes Galaxy Connect re-detect this device.',
    apply: 'Apply', backup: 'Back up', restore: 'Restore', running: 'Running…',
    note: 'Apply and Restore reset Galaxy Connect app data, so you will need to sign in to your Samsung account again.',
    status: 'Status', refresh: 'Refresh', viewLog: 'View log', close: 'Close',
    rows: { detection: 'Galaxy Connect detection', gc: 'Galaxy Connect version', mc: 'Multi Control version', service: 'Service' },
    notInstalled: 'Not installed', none: 'None',
    service: { Running: 'Running', Stopped: 'Stopped' },
    log: 'Activity log', logEmpty: 'Nothing logged yet.',
    footer: 'Unofficial · Not affiliated with Samsung · You are responsible for running it',
    done: { ok: 'Done.', cancelled: 'The administrator prompt was cancelled.', failed: 'Something went wrong. Check the log.' },
    consent: {
      title: 'Before you continue',
      points: [
        'This program changes the manufacturer value in the registry so Galaxy Connect recognizes this PC as a Samsung PC.',
        'You are solely responsible for any consequences of running it. The authors accept no liability for any damage.',
        'This may not comply with Samsung terms of service and could affect your account.',
      ],
      agree: 'I understand and agree to the above', quit: 'Quit', start: 'Agree and start',
    },
    confirm: {
      apply: { title: 'Apply now?', body: 'Galaxy Connect app data will be reset. Afterwards, launch Galaxy Connect and sign in to your Samsung account again.' },
      restore: { title: 'Restore original values?', body: 'The registry is restored and Galaxy Connect app data is reset. Galaxy Connect and Multi Control will no longer work on this PC.' },
      cancel: 'Cancel', ok: 'Continue',
    },
  },
};

export const LANGS = [['ko', '한국어'], ['en', 'English']];

export function defaultLang() {
  return (navigator.language || 'en').toLowerCase().startsWith('ko') ? 'ko' : 'en';
}
