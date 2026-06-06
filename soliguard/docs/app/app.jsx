/* ============================================================
   SoliGuard — App root (window chrome, routing, state machine)
   ============================================================ */

const SCANNED_BY_SCOPE = { full: 2050, quick: 642, closing: 1180 };

function makeSummary(role, scope) {
  return { rows: flattenFindings(DATASETS[role]), when: '3일 전', scanned: 1284 };
}

function initState() {
  let roles = ['개발자'];
  let onboard = null;
  try { onboard = JSON.parse(localStorage.getItem('soliguard_onboard') || 'null'); } catch (e) {}
  if (onboard && Array.isArray(onboard.roles) && onboard.roles.length) roles = onboard.roles;
  const rows = flattenFindings(mergeDataset(roles));
  return {
    view: 'dashboard',
    roles,
    scanScope: 'full',
    heroStyle: 'donut',
    scanFresh: false,
    lastSummary: { rows, when: '3일 전', scanned: 1284 },
    prevTotal: rows.length + 6,
    nextScan: onboard && onboard.nextScan ? onboard.nextScan : '6/9(월) 09:00',
    quarantine: [],
    rolePopover: false,
    completeData: null,
    activity: [
      { icon: 'search', tone: 'brand', title: '전체 스캔 — 위험 12건 발견', when: '3일 전 · 6/3 14:20', right: '개발자' },
      { icon: 'lock', tone: 'brand', title: '격리 — 3개 파일', when: '5일 전 · 6/1 11:05' },
      { icon: 'shieldCheck', tone: 'safe', title: '프로젝트 클로징 점검 완료', when: '9일 전 · 5/28 18:40' },
    ],
    auditLog: [
      { type: 'scan', icon: 'search', tone: 'brand', title: '전체 스캔 실행', detail: '개발자 프로파일 · 2,050개 검사 · 위험 12건', when: '6/3 14:20' },
      { type: 'action', icon: 'lock', tone: 'brand', title: '격리 처리', detail: 'config.prod.yml 외 2건 · 암호화 보관', when: '6/3 14:25' },
      { type: 'action', icon: 'eyeOff', tone: 'brand', title: '마스킹 처리', detail: '회의록_0312.docx · 전화·이메일 5건', when: '6/1 11:05' },
      { type: 'scan', icon: 'folderPlus', tone: 'safe', title: '프로젝트 클로징 점검', detail: '고객사A · 잔여 데이터 정리 완료 · 진단서 발급', when: '5/28 18:40' },
      { type: 'action', icon: 'trash', tone: 'danger', title: '완전삭제 처리', detail: 'payment_test.log · 3-pass 덮어쓰기', when: '5/28 18:38' },
    ],
  };
}

function reducer(s, a) {
  switch (a.type) {
    case 'setHero': return { ...s, heroStyle: a.v };
    case 'nav': return { ...s, view: a.v, scanFresh: false, rolePopover: false };
    case 'openRole': return { ...s, rolePopover: true };
    case 'closeRole': return { ...s, rolePopover: false };
    case 'toggleRole': {
      let roles = s.roles.includes(a.role) ? s.roles.filter(r => r !== a.role) : [...s.roles, a.role];
      if (roles.length === 0) roles = [a.role];
      // keep ROLES order
      roles = ROLES.map(r => r.id).filter(id => roles.includes(id));
      const rows = flattenFindings(mergeDataset(roles));
      return { ...s, roles, view: 'dashboard', scanFresh: false,
        lastSummary: { rows, when: '3일 전', scanned: 1284 }, prevTotal: rows.length + 6, quarantine: [] };
    }
    case 'goScanConfig': return { ...s, scanScope: a.scope, view: 'scanConfig' };
    case 'startScan': return { ...s, view: 'scanning' };
    case 'scanDone': return { ...s, view: 'results' };
    case 'goComplete': {
      const { resolved, discovered, roles, remaining } = a.payload;
      const fullRows = flattenFindings(mergeDataset(roles));
      const prevGrade = gradeOf(countBySeverity(fullRows));
      const newGrade = remaining.length ? gradeOf(countBySeverity(remaining)) : 'safe';
      const handled = resolved.masked + resolved.quarantined + resolved.deleted;
      const scanned = SCANNED_BY_SCOPE[s.scanScope] || 2050;
      const now = new Date();
      const stamp = `${now.getMonth() + 1}/${now.getDate()} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
      const label = rolesLabel(roles);
      const newActivity = [{ icon: 'shieldCheck', tone: 'safe', title: `점검 완료 — ${handled}건 처리`, when: `방금 · ${stamp}`, right: label }, ...s.activity];
      const newLog = [
        { type: 'scan', icon: 'search', tone: 'brand', title: `${s.scanScope === 'quick' ? '빠른' : s.scanScope === 'closing' ? '클로징' : '전체'} 스캔 실행`, detail: `${label} 프로파일 · ${scanned.toLocaleString()}개 검사 · 위험 ${discovered}건`, when: stamp },
        ...(resolved.deleted ? [{ type: 'action', icon: 'trash', tone: 'danger', title: '완전삭제 처리', detail: `${resolved.deleted}건 · 3-pass 덮어쓰기`, when: stamp }] : []),
        ...(resolved.quarantined ? [{ type: 'action', icon: 'lock', tone: 'brand', title: '격리 처리', detail: `${resolved.quarantined}건 · 암호화 보관`, when: stamp }] : []),
        ...(resolved.masked ? [{ type: 'action', icon: 'eyeOff', tone: 'brand', title: '마스킹 처리', detail: `${resolved.masked}건`, when: stamp }] : []),
        ...s.auditLog,
      ];
      return { ...s, view: 'complete', scanFresh: true,
        completeData: { resolved, prevGrade, newGrade, handled, remaining, scanned },
        lastSummary: { rows: remaining, when: '방금', scanned }, prevTotal: discovered,
        activity: newActivity, auditLog: newLog };
    }
    case 'finishToHome': return { ...s, view: 'dashboard', scanFresh: true };
    case 'quarantineAdd': return { ...s, quarantine: [...a.items, ...s.quarantine] };
    case 'quarantineRemove': return { ...s, quarantine: s.quarantine.filter(q => !a.ids.includes(q.uid)) };
    case 'quarantineRestore': return { ...s, quarantine: s.quarantine.filter(q => q.uid !== a.uid) };
    default: return s;
  }
}

const SUBTITLE = {
  dashboard: '보안 대시보드', scanConfig: '스캔 설정', scanning: '스캔 진행', results: '점검 결과',
  complete: '점검 완료', quarantine: '격리함', history: '점검 이력', settings: '설정',
};

function App() {
  const [state, dispatch] = React.useReducer(reducer, null, initState);
  const [toasts, setToasts] = React.useState([]);
  const idRef = React.useRef(0);

  // wrap dispatch to capture toast actions
  const D = React.useCallback((a) => {
    if (a.type === 'toast') { const id = ++idRef.current; setToasts(t => [...t, { ...a.toast, id }]); return; }
    dispatch(a);
  }, []);
  const dismiss = (id) => setToasts(t => t.filter(x => x.id !== id));

  const grade = state.lastSummary && state.lastSummary.rows.length ? gradeOf(countBySeverity(state.lastSummary.rows)) : 'safe';
  const v = state.view;

  return (
    <div className="win">
      <TitleBar subtitle={SUBTITLE[v]} grade={grade} />
      <div className="shell">
        <Sidebar view={v} roles={state.roles} qCount={state.quarantine.length} locked={v === 'scanning'}
          onNav={(view) => D({ type: 'nav', v: view })} onRoleClick={() => D({ type: 'openRole' })} />
        <main style={{ flex: 1, minWidth: 0, position: 'relative', background: 'var(--bg)' }}>
          {v === 'dashboard' && <Dashboard state={state} dispatch={D} />}
          {v === 'scanConfig' && <ScanConfig key={state.scanScope} state={state} dispatch={D} />}
          {v === 'scanning' && <Scanning key={Date.now()} state={state} dispatch={D} />}
          {v === 'results' && <Results key={state.roles.join('|')} state={state} dispatch={D} />}
          {v === 'complete' && <Complete state={state} dispatch={D} />}
          {v === 'quarantine' && <Quarantine state={state} dispatch={D} />}
          {v === 'history' && <History state={state} dispatch={D} />}
          {v === 'settings' && <Settings state={state} dispatch={D} />}
        </main>
      </div>

      {state.rolePopover && <RolePopover roles={state.roles} onToggle={(r) => D({ type: 'toggleRole', role: r })} onClose={() => D({ type: 'closeRole' })} />}

      <div className="toast-wrap">
        {toasts.map(t => <Toast key={t.id} t={t} onDismiss={() => dismiss(t.id)} />)}
      </div>
    </div>
  );
}

function Toast({ t, onDismiss }) {
  const [out, setOut] = React.useState(false);
  React.useEffect(() => {
    const a = setTimeout(() => setOut(true), 3600);
    const b = setTimeout(onDismiss, 3850);
    return () => { clearTimeout(a); clearTimeout(b); };
  }, []);
  return (
    <div className={'toast' + (out ? ' out' : '')}>
      <span className="ti" style={{ background: t.tone || 'var(--brand)', color: '#fff' }}><Icon name={t.icon || 'check'} size={14} stroke={2.4} /></span>
      <span>{t.msg}</span>
      {t.undo && <button className="undo" onClick={() => { t.undo(); setOut(true); setTimeout(onDismiss, 200); }}>실행취소</button>}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
