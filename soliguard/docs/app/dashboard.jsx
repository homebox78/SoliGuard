/* ============================================================
   SoliGuard — Dashboard (3 risk-hero variations)
   ============================================================ */

function DonutHero({ counts, total, grade, animate }) {
  const r = 76, sw = 18, C = 2 * Math.PI * r;
  const segs = [
    { v: counts.high, color: 'var(--danger)' },
    { v: counts.medium, color: 'var(--warn)' },
    { v: counts.low, color: 'var(--safe)' },
  ].filter(s => s.v > 0);
  const denom = total || 1;
  let acc = 0;
  const g = GRADE_META[grade];
  const shown = useCountUp(total, 1000, animate);
  return (
    <div style={{ position: 'relative', width: 208, height: 208, flex: 'none' }}>
      <svg width="208" height="208" viewBox="0 0 208 208" style={{ transform: 'rotate(-90deg)' }}>
        <circle cx="104" cy="104" r={r} fill="none" stroke="var(--surface-alt)" strokeWidth={sw} />
        {(total === 0 ? [{ v: 1, color: 'var(--safe)' }] : segs).map((s, i) => {
          const frac = (total === 0 ? 1 : s.v / denom);
          const len = frac * C;
          const el = (
            <circle key={i} cx="104" cy="104" r={r} fill="none" stroke={s.color} strokeWidth={sw}
              strokeLinecap="round"
              strokeDasharray={`${Math.max(0, len - 6)} ${C}`}
              strokeDashoffset={-acc * C}
              style={{ transition: 'stroke-dasharray .9s cubic-bezier(.2,.8,.2,1)' }} />
          );
          acc += frac;
          return el;
        })}
      </svg>
      <div style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', textAlign: 'center' }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: g.color, letterSpacing: '.02em' }}>{g.label}</div>
          <div style={{ fontSize: 46, fontWeight: 800, lineHeight: 1.05, letterSpacing: '-.03em', fontFamily: 'var(--mono)' }}>{shown}</div>
          <div style={{ fontSize: 12, color: 'var(--text-2)', marginTop: -2 }}>위험 항목</div>
        </div>
      </div>
    </div>
  );
}

function ShieldHero({ total, grade, animate }) {
  const g = GRADE_META[grade];
  const shown = useCountUp(total, 1000, animate);
  return (
    <div style={{ position: 'relative', width: 208, height: 208, flex: 'none', display: 'grid', placeItems: 'center' }}>
      <div style={{ position: 'absolute', width: 150, height: 150, borderRadius: '50%', background: g.bg, filter: 'blur(6px)' }} />
      <svg width="170" height="190" viewBox="0 0 24 24" style={{ position: 'relative', filter: `drop-shadow(0 10px 20px ${g.color}44)` }}>
        <defs>
          <linearGradient id="shg" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor={g.color} stopOpacity="0.92" />
            <stop offset="1" stopColor={g.color} />
          </linearGradient>
        </defs>
        <path d="M12 22s8-3.6 8-9.5V5.3l-8-3-8 3v7.2C4 18.4 12 22 12 22z" fill="url(#shg)" stroke={g.color} strokeWidth="0.4" />
      </svg>
      <div style={{ position: 'absolute', textAlign: 'center', color: '#fff', marginTop: -8 }}>
        <div style={{ fontSize: 44, fontWeight: 800, lineHeight: 1, fontFamily: 'var(--mono)' }}>{shown}</div>
        <div style={{ fontSize: 12.5, fontWeight: 700, opacity: .95, marginTop: 2 }}>{grade === 'safe' ? '안전' : '위험 항목'}</div>
      </div>
      <div style={{ position: 'absolute', bottom: 6, fontSize: 13, fontWeight: 800, color: g.color }}>{g.label} 등급</div>
    </div>
  );
}

function NumericHero({ counts, total, grade, animate }) {
  const g = GRADE_META[grade];
  const shown = useCountUp(total, 1000, animate);
  const max = Math.max(counts.high, counts.medium, counts.low, 1);
  const bars = [
    { k: 'high', label: '높음', v: counts.high, color: 'var(--danger)' },
    { k: 'medium', label: '중간', v: counts.medium, color: 'var(--warn)' },
    { k: 'low', label: '낮음', v: counts.low, color: 'var(--safe)' },
  ];
  return (
    <div style={{ flex: 'none', width: 232, display: 'flex', flexDirection: 'column', gap: 14, justifyContent: 'center' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
        <span style={{ fontSize: 64, fontWeight: 800, letterSpacing: '-.04em', lineHeight: .9, color: g.color, fontFamily: 'var(--mono)' }}>{shown}</span>
        <span style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-2)' }}>건</span>
        <span className={'sev ' + (grade === 'danger' ? 'sev-high' : grade === 'warn' ? 'sev-medium' : 'sev-low')} style={{ marginLeft: 'auto', alignSelf: 'center' }}>
          <span className="dot" />{g.label}
        </span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 9 }}>
        {bars.map(b => (
          <div key={b.k} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ width: 30, fontSize: 12, color: 'var(--text-2)', fontWeight: 600 }}>{b.label}</span>
            <div style={{ flex: 1, height: 9, borderRadius: 5, background: 'var(--surface-alt)', overflow: 'hidden' }}>
              <div style={{ width: `${(b.v / max) * 100}%`, height: '100%', borderRadius: 5, background: b.color, transition: 'width .8s cubic-bezier(.2,.8,.2,1)' }} />
            </div>
            <span style={{ width: 18, textAlign: 'right', fontSize: 13, fontWeight: 700, fontFamily: 'var(--mono)' }}>{b.v}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function Dashboard({ state, dispatch }) {
  const { role, lastSummary, heroStyle, scanFresh, nextScan, activity } = state;
  const rows = lastSummary ? lastSummary.rows : [];
  const counts = countBySeverity(rows);
  const total = rows.length;
  const grade = total ? gradeOf(counts) : 'safe';
  const g = GRADE_META[grade];
  const prev = state.prevTotal;

  const heroOpts = [
    { value: 'donut', label: '도넛', icon: 'refresh' },
    { value: 'shield', label: '방패', icon: 'shield' },
    { value: 'numeric', label: '숫자', icon: 'bolt' },
  ];

  return (
    <div className="view" style={{ padding: '28px 32px 36px', height: '100%', overflowY: 'auto' }}>
      <PageHead
        title="보안 대시보드"
        sub={lastSummary ? `마지막 점검 ${lastSummary.when} · ${lastSummary.scanned.toLocaleString()}개 파일 검사` : '아직 점검 기록이 없습니다 — 첫 점검을 시작해 보세요'}
        right={<div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 12, color: 'var(--text-3)', fontWeight: 600 }}>위험 표현</span>
          <Segmented value={heroStyle} options={heroOpts} onChange={v => dispatch({ type: 'setHero', v })} />
        </div>}
      />

      {/* HERO */}
      <div className="card" style={{ padding: 26, display: 'flex', gap: 30, alignItems: 'center', marginBottom: 18,
        background: 'linear-gradient(180deg,#fff,#fff)', position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', right: -60, top: -60, width: 240, height: 240, borderRadius: '50%',
          background: g.bg, opacity: .5, filter: 'blur(8px)' }} />
        <div style={{ position: 'relative', display: 'grid', placeItems: 'center', minWidth: heroStyle === 'numeric' ? 232 : 208 }}>
          {heroStyle === 'donut' && <DonutHero counts={counts} total={total} grade={grade} animate={scanFresh} />}
          {heroStyle === 'shield' && <ShieldHero total={total} grade={grade} animate={scanFresh} />}
          {heroStyle === 'numeric' && <NumericHero counts={counts} total={total} grade={grade} animate={scanFresh} />}
        </div>

        <div style={{ flex: 1, position: 'relative', minWidth: 280 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
            <span style={{ fontSize: 19, fontWeight: 800, letterSpacing: '-.02em' }}>내 PC 개인정보 위험 등급</span>
            <span className={'sev ' + (grade === 'danger' ? 'sev-high' : grade === 'warn' ? 'sev-medium' : 'sev-low')}>
              <span className="dot" />{g.label}
            </span>
          </div>
          <div style={{ color: 'var(--text-2)', fontSize: 13.5, marginBottom: 16 }}>
            {total ? <>주의가 필요한 항목 <b style={{ color: g.color }}>{total}건</b>을 발견했어요. {g.ko}.</> : '점검한 파일에서 위험을 찾지 못했습니다.'}
            {prev != null && total < prev && (
              <span style={{ color: 'var(--safe)', fontWeight: 700, marginLeft: 8, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                <Icon name="chevD" size={14} stroke={2.6} /> 지난 점검 {prev}건 → {total}건
              </span>
            )}
          </div>

          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
            <button className="btn btn-primary btn-lg" onClick={() => dispatch({ type: 'goScanConfig', scope: 'full' })}>
              <Icon name="search" size={19} stroke={2.3} /> 지금 점검하기
            </button>
            <button className="btn btn-ghost btn-lg" onClick={() => dispatch({ type: 'goScanConfig', scope: 'quick' })}>
              <Icon name="bolt" size={18} /> 빠른 점검
            </button>
          </div>

          <div style={{ display: 'flex', gap: 14, marginTop: 18, flexWrap: 'wrap' }}>
            <MiniStat icon="clock" label="다음 자동 점검" value={nextScan} />
            <MiniStat icon="folder" label="점검 직무" value={role} />
            <MiniStat icon="archive" label="격리 보관" value={`${state.quarantine.length}개`} />
          </div>
        </div>
      </div>

      {/* lower row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.55fr 1fr', gap: 18 }}>
        <div className="card card-pad">
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: 14 }}>
            <span style={{ fontWeight: 800, fontSize: 15 }}>최근 활동</span>
            <button className="btn btn-quiet btn-sm" style={{ marginLeft: 'auto' }} onClick={() => dispatch({ type: 'nav', v: 'history' })}>
              전체 보기 <Icon name="chevR" size={14} />
            </button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {activity.map((a, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 13, padding: '11px 0',
                borderTop: i ? '1px solid var(--border)' : 'none' }}>
                <span style={{ width: 34, height: 34, borderRadius: 9, display: 'grid', placeItems: 'center', flex: 'none',
                  background: a.tone === 'danger' ? 'var(--danger-bg)' : a.tone === 'safe' ? 'var(--safe-bg)' : 'var(--pink-50)',
                  color: a.tone === 'danger' ? 'var(--danger)' : a.tone === 'safe' ? 'var(--safe)' : 'var(--brand)' }}>
                  <Icon name={a.icon} size={17} />
                </span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13.5, fontWeight: 600 }}>{a.title}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-3)' }}>{a.when}</div>
                </div>
                {a.right && <span style={{ fontSize: 12.5, color: 'var(--text-2)', fontWeight: 600 }}>{a.right}</span>}
              </div>
            ))}
          </div>
        </div>

        <div className="card card-pad" style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ fontWeight: 800, fontSize: 15, marginBottom: 12 }}>프로젝트 클로징 점검</div>
          <div style={{ color: 'var(--text-2)', fontSize: 13, lineHeight: 1.55, marginBottom: 16 }}>
            프로젝트가 끝나면 잔여 발주처 데이터를 한 번에 정리하고 진단서를 발급하세요.
          </div>
          <div className="trust" style={{ marginTop: 'auto' }}>
            <Icon name="shield" size={16} style={{ marginTop: 1, flex: 'none' }} />
            <span><b>프로젝트가 끝나면, 데이터도 깨끗하게.</b> 검출된 데이터는 외부로 전송되지 않습니다.</span>
          </div>
          <button className="btn btn-ghost" style={{ marginTop: 14 }} onClick={() => dispatch({ type: 'goScanConfig', scope: 'closing' })}>
            <Icon name="folderPlus" size={17} /> 클로징 점검 시작
          </button>
        </div>
      </div>
    </div>
  );
}

function MiniStat({ icon, label, value }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
      <span style={{ width: 32, height: 32, borderRadius: 8, background: 'var(--surface-alt)', color: 'var(--text-2)', display: 'grid', placeItems: 'center', flex: 'none' }}>
        <Icon name={icon} size={16} />
      </span>
      <div>
        <div style={{ fontSize: 11, color: 'var(--text-3)' }}>{label}</div>
        <div style={{ fontSize: 13, fontWeight: 700 }}>{value}</div>
      </div>
    </div>
  );
}

Object.assign(window, { Dashboard });
