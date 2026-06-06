/* ============================================================
   SoliGuard — Install package: desktop → installer → onboarding
   ============================================================ */

/* ---------- shared small bits ---------- */
function Box({ on, sq }) {
  return (
    <span style={{ width: 20, height: 20, borderRadius: sq ? 6 : '50%', flex: 'none', display: 'grid', placeItems: 'center',
      border: '1.7px solid ' + (on ? 'var(--brand)' : 'var(--border-strong)'), background: on ? 'var(--brand)' : '#fff', transition: 'all .12s' }}>
      {on && (sq ? <Icon name="check" size={13} stroke={3} style={{ color: '#fff' }} /> : <span style={{ width: 9, height: 9, borderRadius: '50%', background: '#fff' }} />)}
    </span>
  );
}
function WinControls({ onClose }) {
  return (
    <div className="os-tbtns">
      <button className="os-tbtn"><svg width="11" height="11" viewBox="0 0 11 11"><rect y="5" width="11" height="1.2" fill="currentColor" /></svg></button>
      <button className="os-tbtn"><svg width="11" height="11" viewBox="0 0 11 11" fill="none" stroke="currentColor" strokeWidth="1.1"><rect x="1" y="1" width="9" height="9" /></svg></button>
      <button className="os-tbtn close" onClick={onClose}><svg width="11" height="11" viewBox="0 0 11 11" stroke="currentColor" strokeWidth="1.2"><path d="M1 1l9 9M10 1l-9 9" /></svg></button>
    </div>
  );
}

/* ====================== DESKTOP ====================== */
function Desktop({ installed, running, onOpenSetup, onOpenApp }) {
  const [sel, setSel] = React.useState(null);
  const [startOpen, setStartOpen] = React.useState(false);
  const [hintGone, setHintGone] = React.useState(installed);
  const now = new Date();
  const time = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
  const date = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
  const openSetup = () => { setHintGone(true); onOpenSetup(); };
  const showHint = !installed && !hintGone;
  return (
    <div className="desktop" onClick={() => { setSel(null); setStartOpen(false); }}>
      <div className="desktop-watermark"><Icon name="shieldCheck" size={360} stroke={0.6} /></div>

      <div className="dt-icons" onClick={e => e.stopPropagation()}>
        <div className={'dt-icon' + (sel === 'setup' ? ' sel' : '')} onClick={() => setSel('setup')} onDoubleClick={openSetup} title="더블클릭하여 설치 시작">
          <div style={{ position: 'relative' }}>
            {showHint && <span className="setup-pulse" />}
            <SetupIcon size={50} />
          </div>
          <span className="lbl">SoliGuard_<br />Setup.exe</span>
        </div>
        {installed && (
          <div className={'dt-icon' + (sel === 'app' ? ' sel' : '')} onClick={() => setSel('app')} onDoubleClick={onOpenApp} title="솔리가드 실행">
            <AppIcon size={50} />
            <span className="lbl">솔리가드<br />SoliGuard</span>
          </div>
        )}
        <div className={'dt-icon' + (sel === 'proj' ? ' sel' : '')} onClick={() => setSel('proj')} title="C:\Projects\고객사A">
          <span style={{ position: 'relative', width: 50, height: 50, display: 'grid', placeItems: 'center' }}>
            <svg width="50" height="50" viewBox="0 0 24 24" fill="none"><path d="M3 6.5C3 5.7 3.7 5 4.5 5h4.2l1.8 2h9C20.3 7 21 7.7 21 8.5V18c0 .8-.7 1.5-1.5 1.5h-15C3.7 19.5 3 18.8 3 18V6.5z" fill="#F4C04E"/><path d="M3 9h18v9c0 .8-.7 1.5-1.5 1.5h-15C3.7 19.5 3 18.8 3 18V9z" fill="#F7D070"/></svg>
          </span>
          <span className="lbl">프로젝트_<br />고객사A</span>
        </div>
        <div className={'dt-icon' + (sel === 'pc' ? ' sel' : '')} onClick={() => setSel('pc')} title="내 PC">
          <span style={{ width: 50, height: 50, borderRadius: 12, background: 'rgba(255,255,255,.12)', display: 'grid', placeItems: 'center', color: 'rgba(255,255,255,.9)' }}><Icon name="hardDrive" size={26} /></span>
          <span className="lbl">내 PC</span>
        </div>
        <div className={'dt-icon' + (sel === 'trash' ? ' sel' : '')} onClick={() => setSel('trash')} title="휴지통">
          <span style={{ width: 50, height: 50, borderRadius: 12, background: 'rgba(255,255,255,.12)', display: 'grid', placeItems: 'center', color: 'rgba(255,255,255,.85)' }}><Icon name="trash" size={26} /></span>
          <span className="lbl">휴지통</span>
        </div>
      </div>

      {showHint && (
        <div className="dt-callout" onClick={e => { e.stopPropagation(); openSetup(); }} style={{ cursor: 'pointer' }}>
          <span style={{ width: 28, height: 28, borderRadius: 8, background: 'var(--brand)', color: '#fff', display: 'grid', placeItems: 'center', flex: 'none' }}><Icon name="download" size={15} stroke={2.4} /></span>
          <span><b>SoliGuard_Setup.exe</b>를<br />더블클릭하여 설치를 시작하세요</span>
        </div>
      )}

      {startOpen && (
        <div className="startmenu" onClick={e => e.stopPropagation()}>
          <div className="tb-search" style={{ width: '100%', marginBottom: 14, cursor: 'text' }}><Icon name="search" size={15} /> 앱, 설정, 문서 검색</div>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'rgba(255,255,255,.5)', letterSpacing: '.06em', margin: '4px 4px 8px' }}>고정됨</div>
          <div className="sm-tile" onClick={installed ? onOpenApp : openSetup}>
            <AppIcon size={36} glow={false} />
            <div><div style={{ fontWeight: 700, fontSize: 13.5 }}>솔리가드 SoliGuard</div><div style={{ fontSize: 11.5, color: 'rgba(255,255,255,.6)' }}>{installed ? '개인정보 점검 도구' : '설치되지 않음 — 클릭하여 설치'}</div></div>
          </div>
          <div className="sm-tile" onClick={() => setSel('proj')}>
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none"><path d="M3 6.5C3 5.7 3.7 5 4.5 5h4.2l1.8 2h9C20.3 7 21 7.7 21 8.5V18c0 .8-.7 1.5-1.5 1.5h-15C3.7 19.5 3 18.8 3 18V6.5z" fill="#F4C04E"/><path d="M3 9h18v9c0 .8-.7 1.5-1.5 1.5h-15C3.7 19.5 3 18.8 3 18V9z" fill="#F7D070"/></svg>
            <div><div style={{ fontWeight: 700, fontSize: 13.5 }}>프로젝트_고객사A</div><div style={{ fontSize: 11.5, color: 'rgba(255,255,255,.6)' }}>C:\Projects\고객사A</div></div>
          </div>
        </div>
      )}

      <div className="taskbar" onClick={e => e.stopPropagation()}>
        <div className="tb-start" onClick={() => setStartOpen(o => !o)}>
          <svg width="19" height="19" viewBox="0 0 24 24"><rect x="3" y="3" width="8" height="8" rx="1.2" fill="#5BBEFA"/><rect x="13" y="3" width="8" height="8" rx="1.2" fill="#48D597"/><rect x="3" y="13" width="8" height="8" rx="1.2" fill="#F4C04E"/><rect x="13" y="13" width="8" height="8" rx="1.2" fill="#EE6285"/></svg>
        </div>
        <div className="tb-search"><Icon name="search" size={15} /> 검색</div>
        <div className="tb-divider" />
        {(installed || running) && <div className={'tb-app' + (running ? ' run' : '')} onClick={installed ? onOpenApp : openSetup} title="솔리가드"><AppIcon size={26} glow={false} /></div>}
        <div className="tb-app" title="파일 탐색기"><svg width="22" height="22" viewBox="0 0 24 24" fill="none"><path d="M3 7c0-.8.7-1.5 1.5-1.5h4l1.5 1.8h9c.8 0 1.5.7 1.5 1.5V17c0 .8-.7 1.5-1.5 1.5h-15C3.7 18.5 3 17.8 3 17V7z" fill="#F4C04E"/><path d="M3 9.5h18V17c0 .8-.7 1.5-1.5 1.5h-15C3.7 18.5 3 17.8 3 17V9.5z" fill="#FAD980"/></svg></div>
        <div className="tray">
          <div className="tray-glyphs">
            {/* wifi */}
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M5 12.5a10 10 0 0 1 14 0"/><path d="M8.5 16a5 5 0 0 1 7 0"/><circle cx="12" cy="19" r="1" fill="currentColor" stroke="none"/></svg>
            {/* volume */}
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"><path d="M4 9v6h4l5 4V5L8 9H4z" fill="currentColor"/><path d="M17 9a4 4 0 0 1 0 6" fill="none"/></svg>
            {/* battery */}
            <svg width="22" height="16" viewBox="0 0 28 16" fill="none"><rect x="1" y="3" width="22" height="10" rx="2.5" stroke="currentColor" strokeWidth="1.6"/><rect x="3" y="5" width="15" height="6" rx="1" fill="currentColor"/><rect x="24.5" y="6" width="2" height="4" rx="1" fill="currentColor"/></svg>
          </div>
          <span className="tray-glyphs" style={{ gap: 4 }}>한 <span style={{ fontSize: 10, opacity: .7 }}>A</span></span>
          <span className="clock"><div>{time}</div><div style={{ fontSize: 11, opacity: .85 }}>{date}</div></span>
        </div>
      </div>
    </div>
  );
}

/* ====================== INSTALLER ====================== */
const INST_STEPS = ['환영', '사용권 계약', '설치 위치', '구성요소', '설치', '완료'];

function Installer({ onClose, onFinish }) {
  const [step, setStep] = React.useState(0);
  const [agree, setAgree] = React.useState(false);
  const [opts, setOpts] = React.useState({ desktop: true, startmenu: true, autoscan: true, ocr: true });
  const [runNow, setRunNow] = React.useState(true);
  const next = () => setStep(s => Math.min(5, s + 1));
  const prev = () => setStep(s => Math.max(0, s - 1));

  return (
    <div style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', zIndex: 40, paddingBottom: 48 }}>
      <div className="os-win win-in" style={{ width: 720, height: 484 }}>
        <div className="os-titlebar">
          <AppIcon size={18} glow={false} />
          <span style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--text-2)' }}>솔리가드 설치</span>
          <div style={{ flex: 1 }} />
          <WinControls onClose={onClose} />
        </div>
        <div className="inst-body">
          <div className="inst-rail">
            <Wordmark light />
            <div style={{ fontSize: 11, color: 'rgba(255,255,255,.72)', marginTop: 10, position: 'relative', zIndex: 1, lineHeight: 1.5 }}>
              SI 실무자 개인정보 점검 도구<br />· v1.0.0
            </div>
            <div className="inst-steps">
              {INST_STEPS.map((s, i) => (
                <div key={i} className={'inst-step' + (i === step ? ' active' : i < step ? ' done' : '')}>
                  <span className="num">{i < step ? <Icon name="check" size={12} stroke={3} /> : i + 1}</span>{s}
                </div>
              ))}
            </div>
            <div className="inst-rail-foot"><Icon name="shield" size={13} /> 로컬 전용 · 외부 전송 없음</div>
          </div>

          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
            <div className="inst-content">
              {step === 0 && <InstWelcome />}
              {step === 1 && <InstLicense agree={agree} setAgree={setAgree} />}
              {step === 2 && <InstPath />}
              {step === 3 && <InstComponents opts={opts} setOpts={setOpts} />}
              {step === 4 && <InstProgress opts={opts} onDone={() => setStep(5)} />}
              {step === 5 && <InstDone runNow={runNow} setRunNow={setRunNow} />}
            </div>
            {step !== 4 && (
              <div className="inst-foot">
                <span style={{ fontSize: 12, color: 'var(--text-3)', fontWeight: 600 }}>단계 {Math.min(step + 1, 6)} / 6</span>
                {step < 5 && <button className="btn btn-quiet btn-sm" onClick={onClose}>취소</button>}
                <div style={{ flex: 1 }} />
                {step > 0 && step < 5 && <button className="btn btn-ghost" onClick={prev}><Icon name="chevL" size={15} /> 이전</button>}
                {step < 4 && <button className="btn btn-primary" disabled={step === 1 && !agree} onClick={next}>{step === 3 ? '설치 시작' : '다음'} <Icon name="chevR" size={15} /></button>}
                {step === 5 && <button className="btn btn-primary" onClick={() => onFinish(runNow)}><Icon name="check" size={16} /> 마침</button>}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function InstWelcome() {
  return (
    <div className="fade-up">
      <div style={{ display: 'flex', alignItems: 'center', gap: 15, marginBottom: 16 }}>
        <AppIcon size={54} />
        <div>
          <h1 style={{ margin: 0, fontSize: 21, fontWeight: 800, letterSpacing: '-.02em' }}>솔리가드 설치를 시작합니다</h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginTop: 6 }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 11.5, fontWeight: 700, color: 'var(--safe)', background: 'var(--safe-bg)', padding: '3px 9px', borderRadius: 999 }}>
              <Icon name="shieldCheck" size={13} /> 디지털 서명 확인됨
            </span>
            <span style={{ fontSize: 11.5, color: 'var(--text-3)' }}>게시자 solideo</span>
          </div>
        </div>
      </div>
      <p style={{ color: 'var(--text-2)', fontSize: 13.5, lineHeight: 1.65, margin: 0 }}>
        설치형 도구로, 내 PC에 흩어진 개인정보·민감정보를 <b>스캔·검출하고 마스킹·격리·삭제</b>합니다. 모든 작업은 <b>설치 PC 로컬</b>에서만 수행됩니다.
      </p>
      <div style={{ display: 'flex', gap: 0, marginTop: 16, marginBottom: 16, padding: '12px 18px', borderRadius: 12, background: 'var(--surface-alt)', border: '1px solid var(--border)', fontSize: 12.5 }}>
        <div style={{ flex: 1 }}><div style={{ color: 'var(--text-3)', fontSize: 11, marginBottom: 2 }}>버전</div><b className="mono">1.0.0</b></div>
        <div style={{ width: 1, background: 'var(--border)', margin: '0 18px' }} />
        <div style={{ flex: 1 }}><div style={{ color: 'var(--text-3)', fontSize: 11, marginBottom: 2 }}>설치 용량</div><b className="mono">312 MB</b></div>
        <div style={{ width: 1, background: 'var(--border)', margin: '0 18px' }} />
        <div style={{ flex: 1.4 }}><div style={{ color: 'var(--text-3)', fontSize: 11, marginBottom: 2 }}>지원 OS</div><b>Windows 10 / 11</b></div>
      </div>
      <div style={{ display: 'flex', gap: 9, flexWrap: 'wrap' }}>
        {['한글(HWP) 2020 호환', 'Tesseract 한국어 OCR 포함', '관리자 권한 필요'].map(c => (
          <span key={c} style={{ display: 'inline-flex', alignItems: 'center', gap: 7, padding: '8px 13px', borderRadius: 10, border: '1px solid var(--border)', background: '#fff', fontSize: 12.5, fontWeight: 600, color: 'var(--text-2)' }}>
            <Icon name="check" size={14} stroke={2.6} style={{ color: 'var(--safe)' }} /> {c}
          </span>
        ))}
      </div>
    </div>
  );
}

function InstLicense({ agree, setAgree }) {
  const arts = [
    ['제1조 (목적)', '본 소프트웨어는 SI 사업장 실무자가 PC 내 개인정보·민감정보를 스스로 점검·조치하기 위한 내부 업무용 도구입니다.'],
    ['제2조 (데이터 처리)', '검출된 모든 데이터와 생성된 리포트는 설치된 PC 로컬 저장소에만 보관되며, 외부 서버로 전송되지 않습니다.'],
    ['제3조 (필수 구성요소)', '본 도구는 한글(HWP) 파서 및 Tesseract 한국어 OCR 런타임이 설치된 환경에서 동작합니다.'],
  ];
  return (
    <div className="fade-up" style={{ display: 'flex', flexDirection: 'column', minHeight: 0, flex: 1 }}>
      <h2 style={{ margin: '0 0 14px', fontSize: 19, fontWeight: 800 }}>사용권 계약</h2>
      <div style={{ flex: 1, overflowY: 'auto', border: '1px solid var(--border)', borderRadius: 12, padding: '16px 18px', background: 'var(--surface-alt)' }}>
        {arts.map(([t, d]) => (
          <div key={t} style={{ marginBottom: 14 }}>
            <div style={{ fontWeight: 700, fontSize: 13.5 }}>{t}</div>
            <div style={{ color: 'var(--text-2)', fontSize: 12.5, lineHeight: 1.6, marginTop: 3 }}>{d}</div>
          </div>
        ))}
      </div>
      <button className="chk-card" style={{ marginTop: 14 }} onClick={() => setAgree(!agree)}>
        <Box on={agree} sq /><span style={{ fontSize: 13.5, fontWeight: 600 }}>위 사용권 계약에 동의합니다.</span>
      </button>
    </div>
  );
}

function InstPath() {
  return (
    <div className="fade-up">
      <h2 style={{ margin: '0 0 6px', fontSize: 19, fontWeight: 800 }}>설치 위치</h2>
      <p style={{ color: 'var(--text-2)', fontSize: 13, marginBottom: 18 }}>솔리가드를 설치할 폴더를 선택하세요.</p>
      <label style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--text-2)' }}>설치 폴더</label>
      <div style={{ display: 'flex', gap: 8, marginTop: 7 }}>
        <input className="fld mono" defaultValue="C:\\Program Files\\SoliGuard" style={{ flex: 1 }} />
        <button className="btn btn-ghost"><Icon name="folder" size={16} /> 찾아보기</button>
      </div>
      <div style={{ display: 'flex', gap: 20, marginTop: 20, fontSize: 12.5, color: 'var(--text-2)' }}>
        <div><span style={{ color: 'var(--text-3)' }}>필요 공간</span> <b className="mono">312 MB</b></div>
        <div><span style={{ color: 'var(--text-3)' }}>사용 가능</span> <b className="mono">84.6 GB</b></div>
      </div>
    </div>
  );
}

function InstComponents({ opts, setOpts }) {
  const t = (k) => setOpts(o => ({ ...o, [k]: !o[k] }));
  const items = [
    ['desktop', 'folder', '바탕화면 아이콘 생성', '바탕화면에 솔리가드 바로가기를 만듭니다'],
    ['startmenu', 'home', '시작 메뉴 바로가기 등록', '시작 메뉴에서 빠르게 실행할 수 있습니다'],
    ['autoscan', 'clock', '주 1회 자동 점검 사용 (권장)', '매주 월요일 09:00, 작업 스케줄러에 등록됩니다'],
    ['ocr', 'image', 'Tesseract 한국어 OCR 포함', '이미지 속 신분증·계약서 검사에 필요합니다'],
  ];
  return (
    <div className="fade-up">
      <h2 style={{ margin: '0 0 6px', fontSize: 19, fontWeight: 800 }}>구성요소 선택</h2>
      <p style={{ color: 'var(--text-2)', fontSize: 13, marginBottom: 16 }}>설치할 항목을 선택하세요.</p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 9 }}>
        {items.map(([k, ic, t1, t2]) => (
          <button key={k} className={'chk-card' + (opts[k] ? ' on' : '')} onClick={() => t(k)}>
            <Box on={opts[k]} sq />
            <Icon name={ic} size={18} style={{ color: opts[k] ? 'var(--brand)' : 'var(--text-3)', marginTop: 1, flex: 'none' }} />
            <span style={{ flex: 1 }}>
              <span style={{ fontSize: 13.5, fontWeight: 700, display: 'block' }}>{t1}</span>
              <span style={{ fontSize: 12, color: 'var(--text-2)', display: 'block', marginTop: 1 }}>{t2}</span>
            </span>
          </button>
        ))}
      </div>
      <div className="trust" style={{ marginTop: 14 }}>
        <Icon name="shield" size={15} style={{ marginTop: 1, flex: 'none' }} />
        <span>설치 시 관리자 권한(UAC) 요청 창이 나타나면 “예”를 눌러 진행하세요.</span>
      </div>
    </div>
  );
}

function InstProgress({ opts, onDone }) {
  const [pct, setPct] = React.useState(0);
  const lines = React.useMemo(() => {
    const base = [
      '파일 압축 해제 중...',
      '검출 엔진 설치 (detectors · scanner · engine)',
      '한글(HWP) 파서 구성요소 등록',
    ];
    if (opts.ocr) base.push('Tesseract 한국어 OCR 데이터 배치');
    if (opts.desktop) base.push('바탕화면 바로가기 생성');
    if (opts.startmenu) base.push('시작 메뉴 등록');
    if (opts.autoscan) base.push('작업 스케줄러에 주간 점검(월 09:00) 등록');
    base.push('설치 마무리 중...');
    return base;
  }, []);
  const [li, setLi] = React.useState(0);
  React.useEffect(() => {
    const t0 = Date.now(); const DUR = 3400;
    const id = setInterval(() => {
      const p = Math.min(1, (Date.now() - t0) / DUR);
      setPct(Math.round(p * 100));
      setLi(Math.min(lines.length - 1, Math.floor(p * lines.length)));
      if (p >= 1) { clearInterval(id); setTimeout(onDone, 400); }
    }, 60);
    return () => clearInterval(id);
  }, []);
  return (
    <div className="fade-up" style={{ display: 'flex', flexDirection: 'column', height: '100%', justifyContent: 'center' }}>
      <h2 style={{ margin: '0 0 6px', fontSize: 19, fontWeight: 800 }}>설치 중…</h2>
      <p className="mono" style={{ color: 'var(--text-2)', fontSize: 12.5, marginBottom: 16, minHeight: 18 }}>{lines[li]}</p>
      <div style={{ display: 'flex', alignItems: 'baseline', marginBottom: 8 }}>
        <span style={{ fontSize: 12.5, color: 'var(--text-3)' }}>진행률</span>
        <span style={{ marginLeft: 'auto', fontFamily: 'var(--mono)', fontWeight: 800, fontSize: 24, color: 'var(--brand)' }}>{pct}%</span>
      </div>
      <div style={{ height: 14, borderRadius: 8, background: 'var(--surface-alt)', overflow: 'hidden' }}>
        <div style={{ width: pct + '%', height: '100%', borderRadius: 8, background: 'linear-gradient(90deg,var(--brand),var(--brand-strong))', transition: 'width .2s linear' }} />
      </div>
    </div>
  );
}

function InstDone({ runNow, setRunNow }) {
  return (
    <div className="fade-up" style={{ display: 'flex', flexDirection: 'column', height: '100%', justifyContent: 'center' }}>
      <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'var(--safe-bg)', color: 'var(--safe)', display: 'grid', placeItems: 'center', marginBottom: 16 }}>
        <Icon name="checkCircle" size={36} stroke={2} />
      </div>
      <h2 style={{ margin: 0, fontSize: 21, fontWeight: 800 }}>설치가 완료되었습니다</h2>
      <p style={{ color: 'var(--text-2)', fontSize: 13.5, marginTop: 8, lineHeight: 1.6 }}>
        솔리가드가 설치되었습니다. 처음 실행하면 직무에 맞춘 초기 설정을 안내합니다.
      </p>
      <button className="chk-card on" style={{ marginTop: 18, maxWidth: 360 }} onClick={() => setRunNow(!runNow)}>
        <Box on={runNow} sq /><span style={{ fontSize: 13.5, fontWeight: 700 }}>지금 솔리가드 실행</span>
      </button>
    </div>
  );
}

/* ====================== ONBOARDING ====================== */
const ONB_STEPS = ['환영', '직무 선택', '스캔 폴더', '자동 점검', '이미지 검사'];

function Onboarding({ onClose }) {
  const [step, setStep] = React.useState(0);
  const [roles, setRoles] = React.useState(['개발자']);
  const [ocr, setOcr] = React.useState(true);
  const [sched, setSched] = React.useState('weekly');
  const cfg = mergeConfig(roles);
  const [folders, setFolders] = React.useState(null);
  const fld = folders || cfg.folders.map(f => ({ path: f, on: true }));
  React.useEffect(() => { setFolders(null); }, [roles]);

  const toggleRole = (r) => setRoles(rs => {
    let n = rs.includes(r) ? rs.filter(x => x !== r) : [...rs, r];
    if (!n.length) n = [r];
    return ROLES.map(x => x.id).filter(id => n.includes(id));
  });
  const SCHED_LABEL = { off: '사용 안 함', daily: '매일 09:00', weekly: '매주 월요일 09:00', monthly: '매월 1일 09:00' };
  const NEXT = { off: '사용 안 함', daily: '내일 09:00', weekly: '6/9(월) 09:00', monthly: '7/1 09:00' };

  const finish = () => {
    try {
      localStorage.setItem('soliguard_onboard', JSON.stringify({
        roles, ocr, schedule: sched, nextScan: NEXT[sched],
      }));
    } catch (e) {}
    window.location.href = 'SoliGuard.html';
  };
  const last = step === ONB_STEPS.length - 1;

  return (
    <div style={{ position: 'absolute', inset: 0, background: 'rgba(16,8,12,.5)', backdropFilter: 'blur(3px)', display: 'grid', placeItems: 'center', zIndex: 45, paddingBottom: 48 }}>
      <div className="os-win win-in" style={{ width: 640, maxHeight: '90%' }}>
        <div className="os-titlebar">
          <AppIcon size={18} glow={false} />
          <span style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--text-2)' }}>솔리가드 — 초기 설정</span>
          <div style={{ flex: 1 }} />
          <WinControls onClose={onClose} />
        </div>

        {/* progress dots */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '16px 26px 6px' }}>
          {ONB_STEPS.map((s, i) => (
            <React.Fragment key={i}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                <span style={{ width: 24, height: 24, borderRadius: '50%', display: 'grid', placeItems: 'center', fontSize: 11, fontWeight: 700, flex: 'none',
                  background: i < step ? 'var(--brand)' : i === step ? 'var(--brand)' : 'var(--surface-alt)', color: i <= step ? '#fff' : 'var(--text-3)' }}>
                  {i < step ? <Icon name="check" size={12} stroke={3} /> : i + 1}
                </span>
                {i === step && <span style={{ fontSize: 12.5, fontWeight: 700, color: 'var(--brand)' }}>{s}</span>}
              </div>
              {i < ONB_STEPS.length - 1 && <span style={{ flex: 1, height: 2, borderRadius: 2, background: i < step ? 'var(--brand)' : 'var(--border)' }} />}
            </React.Fragment>
          ))}
        </div>

        <div className="scroll" style={{ padding: '14px 26px 20px', minHeight: 300, maxHeight: 440 }}>
          {step === 0 && <OnbWelcome />}
          {step === 1 && <OnbRoles roles={roles} toggleRole={toggleRole} />}
          {step === 2 && <OnbFolders fld={fld} setFolders={setFolders} roles={roles} />}
          {step === 3 && <OnbSchedule sched={sched} setSched={setSched} label={SCHED_LABEL} />}
          {step === 4 && <OnbOcr ocr={ocr} setOcr={setOcr} />}
        </div>

        <div className="inst-foot">
          {step > 0 && <button className="btn btn-ghost" onClick={() => setStep(s => s - 1)}><Icon name="chevL" size={15} /> 이전</button>}
          <div style={{ flex: 1 }} />
          {!last && <button className="btn btn-primary" onClick={() => setStep(s => s + 1)}>다음 <Icon name="chevR" size={15} /></button>}
          {last && <button className="btn btn-primary btn-lg" onClick={finish}><Icon name="search" size={17} /> 지금 첫 점검 시작</button>}
        </div>
      </div>
    </div>
  );
}

function OnbWelcome() {
  const promises = [
    ['shield', '로컬 처리', '이 PC 안에서만 처리하고 외부로 전송하지 않습니다'],
    ['checkCircle', '정확한 검출', '체크섬·Luhn·엔트로피 2단계 검증으로 오탐을 줄입니다'],
    ['fileText', '법규 증빙', '발주처 감사·개인정보보호법 대응 리포트를 발급합니다'],
  ];
  return (
    <div className="fade-up" style={{ textAlign: 'center' }}>
      <div style={{ display: 'grid', placeItems: 'center', marginBottom: 12 }}><AppIcon size={56} /></div>
      <h1 style={{ margin: 0, fontSize: 22, fontWeight: 800, letterSpacing: '-.02em' }}>내 PC의 고객 데이터, 먼저 찾습니다</h1>
      <p style={{ color: 'var(--text-2)', fontSize: 13.5, marginTop: 8 }}>프로젝트가 끝나면, 데이터도 깨끗하게 — 솔리가드</p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 12, marginTop: 18, textAlign: 'left' }}>
        {promises.map(([ic, t, d]) => (
          <div key={t} className="card" style={{ padding: 16 }}>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: 'var(--pink-50)', color: 'var(--brand)', display: 'grid', placeItems: 'center', marginBottom: 10 }}><Icon name={ic} size={19} /></div>
            <div style={{ fontWeight: 700, fontSize: 13.5 }}>{t}</div>
            <div style={{ fontSize: 12, color: 'var(--text-2)', marginTop: 4, lineHeight: 1.5, minHeight: 36 }}>{d}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function OnbRoles({ roles, toggleRole }) {
  return (
    <div className="fade-up">
      <h2 style={{ margin: '0 0 4px', fontSize: 19, fontWeight: 800 }}>어떤 업무를 하시나요?</h2>
      <p style={{ color: 'var(--text-2)', fontSize: 13, marginBottom: 16 }}>선택한 직무에 맞춰 점검 항목을 구성합니다. <b style={{ color: 'var(--brand)' }}>복수 선택</b>할 수 있어요.</p>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 9 }}>
        {ROLES.map(r => {
          const on = roles.includes(r.id);
          return (
            <button key={r.id} className={'chk-card' + (on ? ' on' : '')} onClick={() => toggleRole(r.id)}>
              <Box on={on} sq />
              <span style={{ width: 34, height: 34, borderRadius: 9, background: on ? 'var(--brand)' : 'var(--surface-alt)', color: on ? '#fff' : 'var(--text-2)', display: 'grid', placeItems: 'center', flex: 'none' }}><Icon name={r.icon} size={18} /></span>
              <span style={{ flex: 1, minWidth: 0, textAlign: 'left' }}>
                <span style={{ fontSize: 12.2, fontWeight: 700, color: on ? 'var(--brand)' : 'var(--text)', display: 'block', whiteSpace: 'nowrap' }}>{r.id}</span>
                <span style={{ fontSize: 10.4, color: 'var(--text-2)', display: 'block', lineHeight: 1.4, marginTop: 2, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{r.desc}</span>
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function OnbFolders({ fld, setFolders, roles }) {
  const toggle = (i) => setFolders(fld.map((f, j) => j === i ? { ...f, on: !f.on } : f));
  return (
    <div className="fade-up">
      <h2 style={{ margin: '0 0 4px', fontSize: 19, fontWeight: 800 }}>스캔할 폴더를 확인하세요</h2>
      <p style={{ color: 'var(--text-2)', fontSize: 13, marginBottom: 16 }}>직무 “{rolesLabel(roles)}”에 맞춰 추천 폴더가 미리 선택돼 있어요.</p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {fld.map((f, i) => (
          <button key={i} className={'chk-card' + (f.on ? ' on' : '')} style={{ padding: '11px 13px' }} onClick={() => toggle(i)}>
            <Box on={f.on} sq />
            <Icon name="folder" size={17} style={{ color: f.on ? 'var(--brand)' : 'var(--text-3)', flex: 'none' }} />
            <span className="mono" style={{ fontSize: 12.5, color: 'var(--text)' }}>{f.path}</span>
          </button>
        ))}
        <button className="btn btn-ghost btn-sm" style={{ alignSelf: 'flex-start', marginTop: 4 }}><Icon name="plus" size={14} /> 폴더 추가</button>
      </div>
    </div>
  );
}

function OnbSchedule({ sched, setSched, label }) {
  return (
    <div className="fade-up">
      <h2 style={{ margin: '0 0 4px', fontSize: 19, fontWeight: 800 }}>자동 점검 주기를 설정하세요</h2>
      <p style={{ color: 'var(--text-2)', fontSize: 13, marginBottom: 16 }}>정해진 주기에 백그라운드에서 자동으로 PC를 점검합니다.</p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {[['off', '사용 안 함'], ['daily', '매일'], ['weekly', '매주 (월요일) 09:00'], ['monthly', '매월 1일']].map(([k, t]) => (
          <button key={k} className={'chk-card' + (sched === k ? ' on' : '')} style={{ padding: '12px 14px', alignItems: 'center' }} onClick={() => setSched(k)}>
            <Box on={sched === k} />
            <Icon name="clock" size={17} style={{ color: sched === k ? 'var(--brand)' : 'var(--text-3)', flex: 'none' }} />
            <span style={{ fontSize: 13.5, fontWeight: 600 }}>{t}</span>
            {k === 'weekly' && <span className="sev sev-low" style={{ marginLeft: 'auto' }}>권장</span>}
          </button>
        ))}
      </div>
    </div>
  );
}

function OnbOcr({ ocr, setOcr }) {
  return (
    <div className="fade-up">
      <h2 style={{ margin: '0 0 4px', fontSize: 19, fontWeight: 800 }}>이미지 속 정보도 검사할까요?</h2>
      <p style={{ color: 'var(--text-2)', fontSize: 13, marginBottom: 16 }}>시안·스캔본 이미지 속 신분증·계약서를 OCR로 검출합니다.</p>
      <button className={'chk-card' + (ocr ? ' on' : '')} style={{ padding: '16px 16px', alignItems: 'center' }} onClick={() => setOcr(!ocr)}>
        <span style={{ width: 44, height: 44, borderRadius: 11, background: ocr ? 'var(--brand)' : 'var(--surface-alt)', color: ocr ? '#fff' : 'var(--text-3)', display: 'grid', placeItems: 'center', flex: 'none' }}><Icon name="image" size={22} /></span>
        <span style={{ flex: 1 }}>
          <span style={{ fontSize: 14, fontWeight: 700, display: 'block' }}>이미지 속 신분증·계약서 검사 (로컬 OCR)</span>
          <span style={{ fontSize: 12, color: 'var(--text-2)' }}>이미지는 PC를 벗어나지 않고 로컬에서 분석됩니다</span>
        </span>
        <Box on={ocr} />
      </button>
      <div className="trust" style={{ marginTop: 14 }}>
        <Icon name="shield" size={15} style={{ marginTop: 1, flex: 'none' }} />
        <span>외부 OCR API는 이미지가 PC를 벗어나므로 기본 비활성입니다. 필요 시 설정에서 <b>명시적 동의</b> 후에만 켤 수 있습니다.</span>
      </div>
    </div>
  );
}

/* ====================== ROOT ====================== */
function InstallApp() {
  const [stage, setStage] = React.useState('desktop'); // desktop | installer | onboarding
  const [installed, setInstalled] = React.useState(false);

  return (
    <React.Fragment>
      <Desktop installed={installed} running={stage !== 'desktop'}
        onOpenSetup={() => setStage('installer')}
        onOpenApp={() => setStage('onboarding')} />
      {stage === 'installer' && <Installer onClose={() => setStage('desktop')}
        onFinish={(runNow) => { setInstalled(true); setStage(runNow ? 'onboarding' : 'desktop'); }} />}
      {stage === 'onboarding' && <Onboarding onClose={() => setStage('desktop')} />}
    </React.Fragment>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<InstallApp />);
