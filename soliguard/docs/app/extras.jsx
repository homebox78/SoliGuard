/* ============================================================
   SoliGuard — Quarantine · History · Settings
   ============================================================ */

function Quarantine({ state, dispatch }) {
  const items = state.quarantine;
  return (
    <div className="view" style={{ padding: '28px 32px 36px', height: '100%', overflowY: 'auto' }}>
      <PageHead title="격리함" sub="격리된 파일은 암호화되어 안전하게 보관됩니다. 언제든 원래 위치로 복원할 수 있어요." />
      {items.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '70px 20px' }}>
          <div style={{ width: 72, height: 72, borderRadius: '50%', background: 'var(--surface-alt)', color: 'var(--text-3)', display: 'grid', placeItems: 'center', margin: '0 auto 16px' }}>
            <Icon name="lock" size={34} stroke={1.8} />
          </div>
          <div style={{ fontSize: 16, fontWeight: 700 }}>격리된 파일이 없습니다</div>
          <div style={{ color: 'var(--text-2)', fontSize: 13, marginTop: 6 }}>점검 결과에서 위험 항목을 격리하면 여기에 보관됩니다.</div>
        </div>
      ) : (
        <div className="card" style={{ overflow: 'hidden' }}>
          {items.map((it, i) => (
            <div key={it.uid + i} style={{ display: 'flex', alignItems: 'center', gap: 13, padding: '14px 18px', borderTop: i ? '1px solid var(--border)' : 'none' }}>
              <span style={{ width: 38, height: 38, borderRadius: 10, background: 'var(--pink-50)', color: 'var(--brand)', display: 'grid', placeItems: 'center', flex: 'none' }}>
                <Icon name="lock" size={18} />
              </span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 700, fontSize: 13.5 }}>{it.file}</div>
                <div className="mono" style={{ fontSize: 11.5, color: 'var(--text-3)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{it.path}</div>
              </div>
              <div style={{ width: 130 }}>
                <div style={{ fontSize: 12, color: 'var(--text-2)', fontWeight: 600 }}>{it.kind}</div>
                <div style={{ fontSize: 11, color: 'var(--text-3)' }}>{it.when || '방금'}</div>
              </div>
              <SevTag severity={it.severity} />
              <button className="btn btn-ghost btn-sm" onClick={() => { dispatch({ type: 'quarantineRestore', uid: it.uid }); dispatch({ type: 'toast', toast: { icon: 'rotate', tone: 'var(--safe)', msg: `${it.file} 을(를) 원래 위치로 복원했어요` } }); }}>
                <Icon name="rotate" size={14} /> 복원
              </button>
              <button className="btn btn-quiet btn-sm" style={{ color: 'var(--danger)' }} onClick={() => dispatch({ type: 'quarantineRemove', ids: [it.uid] })}>
                <Icon name="trash" size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function History({ state, dispatch }) {
  const [filter, setFilter] = React.useState('all');
  const log = state.auditLog;
  const opts = [
    { value: 'all', label: '전체' },
    { value: 'scan', label: '스캔' },
    { value: 'action', label: '조치' },
  ];
  const shown = log.filter(e => filter === 'all' || e.type === filter);
  return (
    <div className="view" style={{ padding: '28px 32px 36px', height: '100%', overflowY: 'auto' }}>
      <PageHead title="점검 이력" sub="모든 스캔·조치 내역이 감사 로그로 기록됩니다. 컴플라이언스 증빙의 근거가 됩니다."
        right={<div style={{ display: 'flex', gap: 10 }}>
          <Segmented value={filter} options={opts} onChange={setFilter} />
          <button className="btn btn-ghost btn-sm" onClick={() => dispatch({ type: 'toast', toast: { icon: 'download', tone: 'var(--brand)', msg: '감사 로그를 내보냈어요 — audit_log.csv' } })}><Icon name="download" size={14} /> 내보내기</button>
        </div>} />
      <div className="card" style={{ overflow: 'hidden' }}>
        {shown.map((e, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '14px 18px', borderTop: i ? '1px solid var(--border)' : 'none' }}>
            <span style={{ width: 36, height: 36, borderRadius: 9, display: 'grid', placeItems: 'center', flex: 'none',
              background: e.tone === 'danger' ? 'var(--danger-bg)' : e.tone === 'safe' ? 'var(--safe-bg)' : 'var(--pink-50)',
              color: e.tone === 'danger' ? 'var(--danger)' : e.tone === 'safe' ? 'var(--safe)' : 'var(--brand)' }}>
              <Icon name={e.icon} size={17} />
            </span>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 13.5, fontWeight: 600 }}>{e.title}</div>
              <div style={{ fontSize: 12, color: 'var(--text-3)' }}>{e.detail}</div>
            </div>
            <span style={{ fontSize: 12, color: 'var(--text-3)', fontFamily: 'var(--mono)' }}>{e.when}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function Settings({ state, dispatch }) {
  const [tab, setTab] = React.useState('general');
  const [ocr, setOcr] = React.useState(mergeConfig(state.roles).ocr);
  const [sched, setSched] = React.useState('weekly');
  const [autoLevel, setAutoLevel] = React.useState('report');
  const tabs = [
    { id: 'general', label: '일반', icon: 'settings' },
    { id: 'scan', label: '스캔', icon: 'search' },
    { id: 'auto', label: '자동 점검', icon: 'clock' },
    { id: 'security', label: '보안', icon: 'shield' },
    { id: 'about', label: '정보', icon: 'fileText' },
  ];
  return (
    <div className="view" style={{ padding: '28px 32px 36px', height: '100%', overflowY: 'auto' }}>
      <PageHead title="설정" />
      <div style={{ display: 'flex', gap: 24 }}>
        <div style={{ width: 180, flex: 'none', display: 'flex', flexDirection: 'column', gap: 2 }}>
          {tabs.map(t => (
            <button key={t.id} className={'nav-item' + (tab === t.id ? ' active' : '')} onClick={() => setTab(t.id)} style={{ height: 40 }}>
              <Icon name={t.icon} size={17} /> {t.label}
            </button>
          ))}
        </div>
        <div style={{ flex: 1, maxWidth: 620 }}>
          {tab === 'general' && <SettingsCard>
            <Row label="직무 프로파일" desc="선택한 직무에 맞춰 스캔 폴더·검출 항목이 구성됩니다">
              <button className="btn btn-ghost btn-sm" onClick={() => dispatch({ type: 'openRole' })}>
                <Icon name={rolesIcon(state.roles)} size={15} /> {rolesLabel(state.roles)} <Icon name="chevD" size={14} />
              </button>
            </Row>
            <Row label="테마" desc="야간 작업이 많다면 다크 모드를 권장합니다">
              <Segmented value="light" options={[{ value: 'light', label: '라이트', icon: 'sparkle' }, { value: 'dark', label: '다크' }]} onChange={() => dispatch({ type: 'toast', toast: { icon: 'sparkle', tone: 'var(--brand)', msg: '이 프로토타입은 라이트 테마로 시연합니다' } })} />
            </Row>
            <Row label="언어" desc=""><span style={{ fontSize: 13, color: 'var(--text-2)', fontWeight: 600 }}>한국어</span></Row>
          </SettingsCard>}

          {tab === 'scan' && <SettingsCard>
            <Row label="기본 스캔 폴더" desc={mergeConfig(state.roles).folders.join('  ·  ')}><span /></Row>
            <Row label="이미지 OCR 검사" desc="이미지 속 신분증·계약서를 로컬에서 분석합니다">
              <Toggle on={ocr} onClick={() => setOcr(!ocr)} />
            </Row>
            <Row label="OCR 처리 방식" desc="외부 API는 이미지가 PC를 벗어나므로 기본 비활성입니다">
              <Segmented value="local" options={[{ value: 'local', label: '로컬(기본)' }, { value: 'cloud', label: '외부 API' }]} onChange={() => dispatch({ type: 'toast', toast: { icon: 'shield', tone: 'var(--brand)', msg: '외부 OCR은 명시적 동의가 필요합니다 — 기본은 로컬 처리입니다' } })} />
            </Row>
            <Row label="파일 형식" desc=""><span className="mono" style={{ fontSize: 12, color: 'var(--text-2)' }}>{mergeConfig(state.roles).exts}</span></Row>
          </SettingsCard>}

          {tab === 'auto' && <SettingsCard>
            <Row label="자동 점검 주기" desc="정해진 주기에 백그라운드에서 자동으로 점검합니다">
              <select value={sched} onChange={e => setSched(e.target.value)} style={selStyle}>
                <option value="off">사용 안 함</option><option value="daily">매일</option><option value="weekly">매주(월) 09:00</option><option value="monthly">매월 1일</option>
              </select>
            </Row>
            <Row label="자동 조치 수준" desc="안전을 위해 자동 완전삭제는 제공하지 않습니다">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <Radio on={autoLevel === 'report'} onClick={() => setAutoLevel('report')} label="발견·리포트만 (권장)" />
                <Radio on={autoLevel === 'quarantine'} onClick={() => setAutoLevel('quarantine')} label="위험 파일 자동 격리" />
              </div>
            </Row>
          </SettingsCard>}

          {tab === 'security' && <SettingsCard>
            <Row label="격리 폴더 위치" desc=""><span className="mono" style={{ fontSize: 12, color: 'var(--text-2)' }}>C:\\ProgramData\\SoliGuard\\quarantine</span></Row>
            <Row label="삭제 정책" desc="완전삭제는 복구 불가능한 덮어쓰기(wiping)로 수행됩니다"><span style={{ fontSize: 13, color: 'var(--text-2)', fontWeight: 600 }}>3-pass 덮어쓰기</span></Row>
            <Row label="감사 로그 내보내기" desc="발주처 보안 감사 증빙으로 활용됩니다">
              <button className="btn btn-ghost btn-sm" onClick={() => dispatch({ type: 'toast', toast: { icon: 'download', tone: 'var(--brand)', msg: '감사 로그를 내보냈어요 — audit_log.csv' } })}><Icon name="download" size={14} /> CSV / PDF</button>
            </Row>
            <div className="trust" style={{ marginTop: 4 }}>
              <Icon name="shield" size={16} style={{ marginTop: 1, flex: 'none' }} />
              <span>격리 암호화 키는 OS 보안 저장소에 분리 보관됩니다. 모든 처리는 <b>이 PC 안에서만</b> 수행됩니다.</span>
            </div>
          </SettingsCard>}

          {tab === 'about' && <SettingsCard>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '18px 20px' }}>
              <div className="sb-logo" style={{ width: 46, height: 46, borderRadius: 12 }}><Icon name="shieldCheck" size={24} stroke={2.2} /></div>
              <div>
                <div style={{ fontWeight: 800, fontSize: 17 }}>솔리가드 <span style={{ color: 'var(--brand)' }}>SoliGuard</span></div>
                <div style={{ fontSize: 12.5, color: 'var(--text-3)' }}>v1.0.0 · solideo</div>
              </div>
            </div>
            <Row label="제품" desc="SI 실무자를 위한 직무 맞춤형 개인정보 자가점검 도구"><span /></Row>
            <Row label="업데이트" desc="최신 버전을 사용 중입니다"><button className="btn btn-ghost btn-sm"><Icon name="refresh" size={14} /> 업데이트 확인</button></Row>
          </SettingsCard>}
        </div>
      </div>
    </div>
  );
}

const selStyle = { height: 36, borderRadius: 8, border: '1px solid var(--border-strong)', padding: '0 12px', fontSize: 13, fontFamily: 'var(--font)', fontWeight: 600, color: 'var(--text)', background: '#fff', cursor: 'pointer' };
function SettingsCard({ children }) { return <div className="card" style={{ overflow: 'hidden' }}>{React.Children.map(children, (c, i) => <div style={{ borderTop: i ? '1px solid var(--border)' : 'none' }}>{c}</div>)}</div>; }
function Row({ label, desc, children }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '16px 20px' }}>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 13.5, fontWeight: 700 }}>{label}</div>
        {desc && <div style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 2 }}>{desc}</div>}
      </div>
      {children}
    </div>
  );
}
function Toggle({ on, onClick }) {
  return <button onClick={onClick} style={{ width: 46, height: 26, borderRadius: 999, border: 'none', cursor: 'pointer', background: on ? 'var(--brand)' : 'var(--border-strong)', position: 'relative', transition: 'background .15s', flex: 'none' }}>
    <span style={{ position: 'absolute', top: 3, left: on ? 23 : 3, width: 20, height: 20, borderRadius: '50%', background: '#fff', transition: 'left .15s', boxShadow: 'var(--sh-sm)' }} />
  </button>;
}
function Radio({ on, onClick, label }) {
  return <button onClick={onClick} style={{ display: 'flex', alignItems: 'center', gap: 9, background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
    <span style={{ width: 18, height: 18, borderRadius: '50%', border: '2px solid ' + (on ? 'var(--brand)' : 'var(--border-strong)'), display: 'grid', placeItems: 'center', flex: 'none' }}>
      {on && <span style={{ width: 9, height: 9, borderRadius: '50%', background: 'var(--brand)' }} />}
    </span>
    <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>{label}</span>
  </button>;
}

Object.assign(window, { Quarantine, History, Settings });
