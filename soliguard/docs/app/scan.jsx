/* ============================================================
   SoliGuard — Scan Config + Scanning (3 progress treatments)
   ============================================================ */

function ScanConfig({ state, dispatch }) {
  const { roles, scanScope } = state;
  const base = mergeConfig(roles);
  const [folders, setFolders] = React.useState(
    base.folders.map((p, i) => ({ path: p, on: scanScope === 'quick' ? i < 2 : true }))
      .concat([{ path: '전체 드라이브 (C:\\)', on: scanScope === 'full' ? false : false, drive: true }]));
  const [kinds, setKinds] = React.useState(() => {
    const def = {};
    ALL_KINDS.forEach(k => def[k] = false);
    base.kinds.forEach(k => {
      const map = { '주민등록번호':'주민등록번호','신용카드':'신용카드','전화/이메일':'전화/이메일','계좌번호':'계좌번호','사업자번호':'사업자번호','DB·API키':'DB·API키','이미지 속 정보(OCR)':'이미지 속 정보(OCR)','한글(hwp) 문서':'한글(hwp) 문서' };
      if (map[k]) def[map[k]] = true;
    });
    return def;
  });
  const closing = scanScope === 'closing';
  const activeFolders = folders.filter(f => f.on).length;
  const activeKinds = Object.values(kinds).filter(Boolean).length;

  const scopeMeta = {
    full:    { label: '전체 스캔', desc: '지정한 폴더와 드라이브를 빠짐없이 검사합니다', icon: 'search' },
    quick:   { label: '빠른 점검', desc: '위험 폴더(다운로드·바탕화면·작업폴더)만 빠르게 훑습니다', icon: 'bolt' },
    closing: { label: '프로젝트 클로징 점검', desc: '프로젝트 폴더의 잔여 발주처 데이터를 일괄 점검·정리합니다', icon: 'folderPlus' },
  }[scanScope];

  return (
    <div className="view" style={{ padding: '28px 32px 36px', height: '100%', overflowY: 'auto' }}>
      <button className="btn btn-quiet btn-sm" style={{ marginBottom: 10, paddingLeft: 6 }} onClick={() => dispatch({ type: 'nav', v: 'dashboard' })}>
        <Icon name="chevL" size={16} /> 대시보드
      </button>
      <PageHead title="스캔 설정" sub={`직무 “${rolesLabel(roles)}” 프로파일 기준으로 기본값이 채워졌어요. 그대로 시작해도 됩니다.`} />

      {/* scope banner */}
      <div className="card" style={{ padding: '14px 18px', display: 'flex', alignItems: 'center', gap: 14, marginBottom: 18,
        background: closing ? 'var(--pink-50)' : '#fff', borderColor: closing ? 'var(--pink-200)' : 'var(--border)' }}>
        <span style={{ width: 40, height: 40, borderRadius: 10, background: 'var(--brand)', color: '#fff', display: 'grid', placeItems: 'center', flex: 'none' }}>
          <Icon name={scopeMeta.icon} size={20} stroke={2.2} />
        </span>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 800, fontSize: 14.5 }}>{scopeMeta.label}</div>
          <div style={{ color: 'var(--text-2)', fontSize: 12.5 }}>{scopeMeta.desc}</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18 }}>
        {/* folders */}
        <div className="card card-pad">
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: 14 }}>
            <span style={{ fontWeight: 800, fontSize: 15 }}>스캔 대상 폴더</span>
            <span style={{ marginLeft: 8, fontSize: 12, color: 'var(--text-3)' }}>{activeFolders}곳 선택</span>
            <button className="btn btn-ghost btn-sm" style={{ marginLeft: 'auto' }}><Icon name="plus" size={15} /> 폴더 추가</button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {folders.map((f, i) => (
              <button key={i} onClick={() => setFolders(fs => fs.map((x, j) => j === i ? { ...x, on: !x.on } : x))}
                style={{ display: 'flex', alignItems: 'center', gap: 11, padding: '11px 12px', borderRadius: 10, cursor: 'pointer',
                  border: '1px solid ' + (f.on ? 'var(--pink-200)' : 'var(--border)'), background: f.on ? 'var(--pink-50)' : '#fff', textAlign: 'left' }}>
                <Check on={f.on} />
                <Icon name={f.drive ? 'hardDrive' : 'folder'} size={17} style={{ color: f.on ? 'var(--brand)' : 'var(--text-3)' }} />
                <span className="mono" style={{ fontSize: 12.5, color: 'var(--text)', flex: 1 }}>{f.path}</span>
              </button>
            ))}
          </div>
        </div>

        {/* kinds */}
        <div className="card card-pad">
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: 6 }}>
            <span style={{ fontWeight: 800, fontSize: 15 }}>검출할 항목</span>
            <span style={{ marginLeft: 8, fontSize: 12, color: 'var(--text-3)' }}>{activeKinds}개 항목</span>
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-3)', marginBottom: 13 }}>직무: {rolesLabel(roles)} 기본값</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {ALL_KINDS.map(k => {
              const special = k === 'DB·API키' || k === '이미지 속 정보(OCR)';
              const on = kinds[k];
              return (
                <button key={k} onClick={() => setKinds(s => ({ ...s, [k]: !s[k] }))}
                  style={{ display: 'inline-flex', alignItems: 'center', gap: 7, padding: '8px 13px 8px 11px', borderRadius: 999, cursor: 'pointer',
                    fontSize: 12.5, fontWeight: 600, whiteSpace: 'nowrap',
                    border: '1px solid ' + (on ? 'var(--brand)' : 'var(--border)'),
                    background: on ? 'var(--brand)' : '#fff', color: on ? '#fff' : 'var(--text-2)' }}>
                  <Icon name={on ? 'check' : 'plus'} size={14} stroke={2.4} /> {k}
                </button>
              );
            })}
          </div>
          {kinds['DB·API키'] && <div style={{ marginTop: 13, fontSize: 12, color: 'var(--brand)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
            <Icon name="key" size={14} /> 개발자 특화 — 소스코드·설정파일의 시크릿을 엔트로피로 검증합니다</div>}
          <div style={{ marginTop: 16, paddingTop: 14, borderTop: '1px solid var(--border)', fontSize: 12, color: 'var(--text-3)' }}>
            <span style={{ fontWeight: 600, color: 'var(--text-2)' }}>파일 형식</span>
            <span className="mono" style={{ marginLeft: 8 }}>{base.exts}</span>
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 22 }}>
        <div className="trust" style={{ flex: 1 }}>
          <Icon name="shield" size={16} style={{ marginTop: 1, flex: 'none' }} />
          <span>스캔은 이 PC 안에서만 수행되며, 검출된 어떤 데이터도 외부로 전송되지 않습니다.</span>
        </div>
        <button className="btn btn-primary btn-lg" disabled={!activeFolders || !activeKinds} onClick={() => dispatch({ type: 'startScan' })}>
          <Icon name="search" size={18} stroke={2.3} /> 스캔 시작
        </button>
      </div>
    </div>
  );
}

function Check({ on }) {
  return (
    <span style={{ width: 19, height: 19, borderRadius: 6, flex: 'none', display: 'grid', placeItems: 'center',
      border: '1.6px solid ' + (on ? 'var(--brand)' : 'var(--border-strong)'), background: on ? 'var(--brand)' : '#fff', transition: 'all .12s' }}>
      {on && <Icon name="check" size={13} stroke={3} style={{ color: '#fff' }} />}
    </span>
  );
}

/* -------------------- Scanning -------------------- */
const DECOY_FILES = [
  'README.md','package.json','main.py','styles.css','util.js','notes.txt','logo.svg',
  'index.html','schema.sql','report_draft.docx','backup_0531.zip','thumbnail.png',
  'invoice_template.xlsx','meeting.ics','build.gradle','.env.example','data_2025.csv',
];

function Scanning({ state, dispatch }) {
  const { roles, scanScope } = state;
  const dataset = mergeDataset(roles);
  const rows = React.useMemo(() => flattenFindings(dataset), [roles]);
  const total = scanScope === 'quick' ? 642 : scanScope === 'closing' ? 1180 : 2050;
  const ocr = mergeConfig(roles).ocr;

  const [style, setStyle] = React.useState('linear');
  const [pct, setPct] = React.useState(0);
  const [paused, setPaused] = React.useState(false);
  const [cur, setCur] = React.useState('파일 수집 중...');
  const pausedRef = React.useRef(false);
  const startRef = React.useRef(0);
  const fileListRef = React.useRef([]);
  const [ticker, setTicker] = React.useState([]);

  // buckets: map kind -> 4 display buckets
  const finalBuckets = React.useMemo(() => {
    const b = { '주민등록번호': 0, '신용카드번호': 0, 'API키/DB': 0, '전화·이메일': 0, '기타': 0 };
    rows.forEach(r => {
      if (r.kind === '주민등록번호' || r.kind === '신분증 이미지' || r.kind === '실고객 샘플') b['주민등록번호']++;
      else if (r.kind === '신용카드번호') b['신용카드번호']++;
      else if (r.kind === 'API키/시크릿' || r.kind === 'DB접속정보') b['API키/DB']++;
      else if (r.kind === '휴대전화번호' || r.kind === '이메일') b['전화·이메일']++;
      else b['기타']++;
    });
    return b;
  }, [rows]);

  const DUR = 5200;
  React.useEffect(() => {
    const allFiles = dataset.map(d => d.file).concat(DECOY_FILES);
    let acc = 0;        // accumulated active ms
    let last = Date.now();
    let done = false;
    const id = setInterval(() => {
      const now = Date.now();
      const dt = now - last; last = now;
      if (pausedRef.current) return;
      acc += dt;
      let p = Math.min(1, acc / DUR);
      if (ocr && p > 0.7 && p < 0.82) p = 0.7 + (p - 0.7) * 0.5; // OCR stall
      setPct(Math.round(p * 100));
      const idx = Math.floor(acc / 230);
      const f = allFiles[idx % allFiles.length];
      const folder = dataset[idx % dataset.length].path;
      if (fileListRef.current[fileListRef.current.length - 1] !== f) {
        fileListRef.current = [...fileListRef.current.slice(-7), f];
        setTicker(fileListRef.current.slice());
        setCur(`${folder}\\${f}`);
      }
      if (p >= 1 && !done) {
        done = true;
        clearInterval(id);
        setCur('분석 완료');
        setTimeout(() => dispatch({ type: 'scanDone' }), 520);
      }
    }, 55);
    return () => clearInterval(id);
  }, []);

  const scanned = Math.round(total * pct / 100);
  const stage = pct < 10 ? 0 : pct < 86 ? 1 : 2;
  const eta = pct >= 100 ? 0 : Math.max(1, Math.ceil((100 - pct) / 100 * (DUR / 1000)));
  const reveal = (final) => Math.round(final * Math.min(1, pct / 92));
  const liveTotal = Object.keys(finalBuckets).reduce((a, k) => a + reveal(finalBuckets[k]), 0);

  const stages = [
    { label: '파일 수집', icon: 'folder' },
    { label: '내용 검사', icon: 'search' },
    { label: '검증·분석', icon: 'cpu' },
  ];
  const buckets = [
    { k: '주민등록번호', icon: 'user', color: 'var(--danger)' },
    { k: '신용카드번호', icon: 'card', color: 'var(--danger)' },
    { k: 'API키/DB', icon: 'key', color: 'var(--warn)' },
    { k: '전화·이메일', icon: 'mail', color: 'var(--info)' },
  ];

  const styleOpts = [
    { value: 'linear', label: '막대형', icon: 'list' },
    { value: 'radial', label: '원형', icon: 'refresh' },
    { value: 'minimal', label: '미니멀', icon: 'bolt' },
  ];

  return (
    <div className="view" style={{ padding: '28px 32px', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 22 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 22, fontWeight: 800, letterSpacing: '-.02em', display: 'flex', alignItems: 'center', gap: 10 }}>
            <Icon name="search" size={22} style={{ color: 'var(--brand)' }} className={pct < 100 ? '' : ''} />
            스캔 진행 중
          </h1>
          <div style={{ color: 'var(--text-2)', fontSize: 13, marginTop: 4 }}>
            {stages[stage].label} · 검사 {scanned.toLocaleString()} / {total.toLocaleString()}개 {pct < 100 && <>· 예상 남은 시간 약 {eta}초</>}
          </div>
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 12, color: 'var(--text-3)', fontWeight: 600 }}>연출</span>
          <Segmented value={style} options={styleOpts} onChange={setStyle} />
        </div>
      </div>

      <div style={{ flex: 1, display: 'grid', placeItems: 'center', minHeight: 0 }}>
        <div style={{ width: '100%', maxWidth: 760 }}>
          {style === 'linear' && <LinearScan pct={pct} stages={stages} stage={stage} cur={cur} />}
          {style === 'radial' && <RadialScan pct={pct} liveTotal={liveTotal} cur={cur} stage={stages[stage].label} />}
          {style === 'minimal' && <MinimalScan pct={pct} ticker={ticker} liveTotal={liveTotal} />}

          {/* live found counts (shared) */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 12, marginTop: 24 }}>
            {buckets.map(b => {
              const v = reveal(finalBuckets[b.k]);
              return (
                <div key={b.k} className="card" style={{ padding: '14px 16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-2)', fontSize: 12, fontWeight: 600 }}>
                    <Icon name={b.icon} size={15} style={{ color: b.color }} /> {b.k}
                  </div>
                  <div style={{ fontSize: 28, fontWeight: 800, fontFamily: 'var(--mono)', marginTop: 4, color: v ? b.color : 'var(--text-3)' }}>{v}</div>
                </div>
              );
            })}
          </div>

          {ocr && pct > 60 && pct < 90 && (
            <div style={{ marginTop: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, color: 'var(--warn)', fontSize: 12.5, fontWeight: 600 }}>
              <span className="spinner" style={{ width: 14, height: 14, border: '2px solid var(--warn-line)', borderTopColor: 'var(--warn)', borderRadius: '50%', display: 'inline-block', animation: 'spin .8s linear infinite' }} />
              이미지 분석 중 — 시간이 조금 걸릴 수 있어요
            </div>
          )}
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'center', gap: 10, marginTop: 8 }}>
        <button className="btn btn-ghost" onClick={() => { pausedRef.current = !pausedRef.current; setPaused(p => !p); }}>
          <Icon name={paused ? 'search' : 'pause'} size={17} /> {paused ? '재개' : '일시정지'}
        </button>
        <button className="btn btn-quiet" onClick={() => dispatch({ type: 'scanDone' })}>
          <Icon name="stop" size={16} /> 중지하고 결과 보기
        </button>
      </div>
    </div>
  );
}

function LinearScan({ pct, stages, stage, cur }) {
  return (
    <div className="card card-pad fade-up">
      <div style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
        {stages.map((s, i) => (
          <div key={i} style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 9, padding: '10px 12px', borderRadius: 10,
            background: i === stage ? 'var(--pink-50)' : i < stage ? '#fff' : 'var(--surface-alt)',
            border: '1px solid ' + (i === stage ? 'var(--pink-200)' : 'var(--border)') }}>
            <span style={{ width: 26, height: 26, borderRadius: 7, display: 'grid', placeItems: 'center', flex: 'none',
              background: i < stage ? 'var(--safe)' : i === stage ? 'var(--brand)' : 'var(--border)', color: i <= stage ? '#fff' : 'var(--text-3)' }}>
              {i < stage ? <Icon name="check" size={15} stroke={3} /> : <Icon name={s.icon} size={15} />}
            </span>
            <span style={{ fontSize: 13, fontWeight: 700, color: i === stage ? 'var(--brand)' : i < stage ? 'var(--text)' : 'var(--text-3)' }}>{s.label}</span>
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', alignItems: 'baseline', marginBottom: 8 }}>
        <span style={{ fontSize: 13, color: 'var(--text-2)', fontWeight: 600 }}>진행률</span>
        <span style={{ marginLeft: 'auto', fontSize: 30, fontWeight: 800, fontFamily: 'var(--mono)', color: 'var(--brand)' }}>{pct}<span style={{ fontSize: 16 }}>%</span></span>
      </div>
      <div style={{ height: 14, borderRadius: 8, background: 'var(--surface-alt)', overflow: 'hidden' }}>
        <div style={{ width: pct + '%', height: '100%', borderRadius: 8, background: 'linear-gradient(90deg,var(--brand),var(--brand-strong))', transition: 'width .25s linear' }} />
      </div>
      <div className="mono" style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 12, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        <span style={{ color: 'var(--text-2)' }}>검사 중</span> {cur}
      </div>
    </div>
  );
}

function RadialScan({ pct, liveTotal, cur, stage }) {
  const r = 92, C = 2 * Math.PI * r;
  return (
    <div className="card card-pad fade-up" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: 30, paddingBottom: 28 }}>
      <div style={{ position: 'relative', width: 230, height: 230 }}>
        <div style={{ position: 'absolute', inset: 18, borderRadius: '50%', background: 'conic-gradient(from 0deg, transparent, var(--pink-100))', animation: 'sweep 1.4s linear infinite', opacity: pct < 100 ? 1 : 0 }} />
        <svg width="230" height="230" viewBox="0 0 230 230" style={{ position: 'relative', transform: 'rotate(-90deg)' }}>
          <circle cx="115" cy="115" r={r} fill="none" stroke="var(--surface-alt)" strokeWidth="14" />
          <circle cx="115" cy="115" r={r} fill="none" stroke="var(--brand)" strokeWidth="14" strokeLinecap="round"
            strokeDasharray={C} strokeDashoffset={C * (1 - pct / 100)} style={{ transition: 'stroke-dashoffset .25s linear' }} />
        </svg>
        <div style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', textAlign: 'center' }}>
          <div>
            <div style={{ fontSize: 48, fontWeight: 800, fontFamily: 'var(--mono)', lineHeight: 1, color: 'var(--brand)' }}>{pct}<span style={{ fontSize: 22 }}>%</span></div>
            <div style={{ fontSize: 12.5, color: 'var(--text-2)', marginTop: 6, fontWeight: 600 }}>{stage}</div>
            <div style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 2 }}>발견 {liveTotal}건</div>
          </div>
        </div>
      </div>
      <div className="mono" style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 18, maxWidth: 520, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{cur}</div>
    </div>
  );
}

function MinimalScan({ pct, ticker, liveTotal }) {
  return (
    <div className="fade-up">
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 16, marginBottom: 18 }}>
        <span style={{ fontSize: 96, fontWeight: 800, fontFamily: 'var(--mono)', lineHeight: .85, letterSpacing: '-.04em', color: 'var(--text)' }}>{pct}<span style={{ fontSize: 38, color: 'var(--brand)' }}>%</span></span>
        <span style={{ marginLeft: 'auto', textAlign: 'right', color: 'var(--text-2)', fontSize: 13 }}>
          <div style={{ fontWeight: 700, color: 'var(--brand)', fontSize: 15 }}>발견 {liveTotal}건</div>
          <div>실시간 검출</div>
        </span>
      </div>
      <div style={{ height: 4, borderRadius: 4, background: 'var(--surface-alt)', overflow: 'hidden', marginBottom: 18 }}>
        <div style={{ width: pct + '%', height: '100%', background: 'var(--brand)', transition: 'width .25s linear' }} />
      </div>
      <div className="card" style={{ padding: '14px 16px', background: '#14161C', border: 'none', fontFamily: 'var(--mono)', fontSize: 12.5, height: 180, overflow: 'hidden', display: 'flex', flexDirection: 'column', justifyContent: 'flex-end' }}>
        {ticker.map((f, i) => (
          <div key={i} style={{ color: i === ticker.length - 1 ? '#FFC9D8' : 'rgba(255,255,255,.4)', padding: '2px 0', opacity: 0.4 + (i / ticker.length) * 0.6 }}>
            <span style={{ color: 'var(--safe)' }}>✓</span> scanned&nbsp;&nbsp;{f}
          </div>
        ))}
      </div>
    </div>
  );
}

Object.assign(window, { ScanConfig, Scanning });
