/* ============================================================
   SoliGuard — shared components
   ============================================================ */

function TitleBar({ subtitle, grade }) {
  const g = GRADE_META[grade] || GRADE_META.safe;
  return (
    <div className="titlebar">
      <div className="tb-icon"><Icon name="shieldCheck" size={12} stroke={2.4} /></div>
      <span className="tb-title">솔리가드 <span className="tb-sep">—</span> {subtitle}</span>
      <div className="tb-spacer" />
      <span className="tb-pill" style={{ color: g.color, background: g.bg }}>
        <span style={{ width: 7, height: 7, borderRadius: '50%', background: g.color, display: 'inline-block' }} />
        로컬 전용 · 외부 전송 없음
      </span>
      <div className="tb-btns">
        <button className="tb-btn" aria-label="최소화"><svg width="11" height="11" viewBox="0 0 11 11"><rect y="5" width="11" height="1.2" fill="currentColor"/></svg></button>
        <button className="tb-btn" aria-label="최대화"><svg width="11" height="11" viewBox="0 0 11 11" fill="none" stroke="currentColor" strokeWidth="1.1"><rect x="1" y="1" width="9" height="9"/></svg></button>
        <button className="tb-btn close" aria-label="닫기"><svg width="11" height="11" viewBox="0 0 11 11" stroke="currentColor" strokeWidth="1.2"><path d="M1 1l9 9M10 1l-9 9"/></svg></button>
      </div>
    </div>
  );
}

const NAV = [
  { id: 'home',       label: '홈',        icon: 'home' },
  { id: 'quarantine', label: '격리함',     icon: 'lock' },
  { id: 'history',    label: '점검 이력',  icon: 'history' },
  { id: 'settings',   label: '설정',       icon: 'settings' },
];

function Sidebar({ view, onNav, roles, onRoleClick, qCount, locked }) {
  const homeViews = ['dashboard','scanConfig','scanning','results','complete'];
  const activeNav = homeViews.includes(view) ? 'home' : view;
  return (
    <aside className="sidebar">
      <div className="sb-brand">
        <div className="sb-logo"><Icon name="shieldCheck" size={19} stroke={2.3} /></div>
        <div>
          <div className="sb-name">솔리<b>가드</b></div>
          <div className="sb-tag">SoliGuard · v1.0</div>
        </div>
      </div>

      <div className="sb-sec">메뉴</div>
      <nav className="sb-nav">
        {NAV.map(n => (
          <button key={n.id} className={'nav-item' + (activeNav === n.id ? ' active' : '')}
            disabled={locked} onClick={() => onNav(n.id === 'home' ? 'dashboard' : n.id)}>
            <Icon name={n.icon} size={18} stroke={activeNav === n.id ? 2.3 : 2} />
            {n.label}
            {n.id === 'quarantine' && qCount > 0 && <span className="nav-badge">{qCount}</span>}
          </button>
        ))}
      </nav>

      <div className="sb-foot">
        <div className="trust-foot"><Icon name="shield" size={13} /> 데이터는 이 PC 안에서만 처리됩니다</div>
        <button className="role-chip" onClick={onRoleClick} disabled={locked}>
          <span className="role-av"><Icon name={rolesIcon(roles)} size={17} /></span>
          <span style={{ flex: 1, minWidth: 0 }}>
            <span className="rc-label">직무 프로파일{roles.length > 1 ? ` · ${roles.length}개` : ''}</span>
            <span className="rc-role" style={{ display: 'block', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{rolesLabel(roles)}</span>
          </span>
          <Icon name="chevR" size={15} style={{ color: 'var(--text-3)', flex: 'none' }} />
        </button>
      </div>
    </aside>
  );
}

function RolePopover({ roles, onToggle, onClose }) {
  const Box = ({ on }) => (
    <span style={{ width: 19, height: 19, borderRadius: 6, flex: 'none', display: 'grid', placeItems: 'center', marginTop: 1,
      border: '1.6px solid ' + (on ? 'var(--brand)' : 'var(--border-strong)'), background: on ? 'var(--brand)' : '#fff' }}>
      {on && <Icon name="check" size={13} stroke={3} style={{ color: '#fff' }} />}
    </span>
  );
  return (
    <div className="overlay" style={{ alignItems: 'flex-end', justifyContent: 'flex-start' }} onClick={onClose}>
      <div className="card pop-in" style={{ width: 360, margin: '0 0 78px 16px', boxShadow: 'var(--sh-pop)', overflow: 'hidden' }} onClick={e => e.stopPropagation()}>
        <div style={{ padding: '16px 18px 10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontWeight: 800, fontSize: 15 }}>직무 프로파일</span>
            <span className="sev sev-low" style={{ fontSize: 10.5, padding: '1px 8px' }}>복수 선택</span>
          </div>
          <div style={{ color: 'var(--text-2)', fontSize: 12.5, marginTop: 3 }}>선택한 모든 직무의 폴더·검출 항목이 합쳐서 구성됩니다.</div>
        </div>
        <div style={{ padding: '4px 10px 10px', display: 'flex', flexDirection: 'column', gap: 2 }}>
          {ROLES.map(r => {
            const on = roles.includes(r.id);
            return (
              <button key={r.id} className="nav-item" style={{ height: 'auto', padding: '11px 12px', alignItems: 'flex-start', background: on ? 'var(--pink-50)' : 'transparent' }}
                onClick={() => onToggle(r.id)}>
                <Box on={on} />
                <span className="role-av" style={{ background: on ? 'var(--brand)' : 'var(--surface-alt)', color: on ? '#fff' : 'var(--text-2)' }}>
                  <Icon name={r.icon} size={17} />
                </span>
                <span style={{ flex: 1, minWidth: 0 }}>
                  <span style={{ fontWeight: 700, color: on ? 'var(--brand)' : 'var(--text)', fontSize: 13.5 }}>{r.id}</span>
                  <span style={{ display: 'block', fontWeight: 400, fontSize: 12, color: 'var(--text-2)', marginTop: 2, whiteSpace: 'normal', lineHeight: 1.45 }}>{r.desc}</span>
                </span>
              </button>
            );
          })}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', padding: '10px 16px', borderTop: '1px solid var(--border)' }}>
          <span style={{ fontSize: 12, color: 'var(--text-3)' }}>{roles.length}개 직무 선택됨</span>
          <button className="btn btn-primary btn-sm" style={{ marginLeft: 'auto' }} onClick={onClose}>적용</button>
        </div>
      </div>
    </div>
  );
}

function Segmented({ value, options, onChange, size }) {
  return (
    <div className="seg" style={size === 'sm' ? { padding: 2 } : {}}>
      {options.map(o => (
        <button key={o.value} className={value === o.value ? 'on' : ''} onClick={() => onChange(o.value)}>
          {o.icon && <Icon name={o.icon} size={14} />}{o.label}
        </button>
      ))}
    </div>
  );
}

function SevTag({ severity, withDot = true }) {
  const m = SEV_META[severity];
  return <span className={'sev ' + m.cls}>{withDot && <span className="dot" />}{m.label}</span>;
}

function PageHead({ title, sub, right }) {
  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 16, marginBottom: 22 }}>
      <div style={{ flex: 1 }}>
        <h1 style={{ margin: 0, fontSize: 23, fontWeight: 800, letterSpacing: '-.02em' }}>{title}</h1>
        {sub && <div style={{ color: 'var(--text-2)', fontSize: 13.5, marginTop: 5 }}>{sub}</div>}
      </div>
      {right}
    </div>
  );
}

/* a value that counts up to `target` over `dur` ms */
function useCountUp(target, dur = 900, run = true) {
  const [v, setV] = React.useState(run ? 0 : target);
  React.useEffect(() => {
    if (!run) { setV(target); return; }
    const t0 = Date.now();
    setV(0);
    const id = setInterval(() => {
      const p = Math.min(1, (Date.now() - t0) / dur);
      const e = 1 - Math.pow(1 - p, 3);
      setV(Math.round(target * e));
      if (p >= 1) clearInterval(id);
    }, 40);
    return () => clearInterval(id);
  }, [target, run]);
  return v;
}

Object.assign(window, { TitleBar, Sidebar, RolePopover, Segmented, SevTag, PageHead, useCountUp, NAV });
