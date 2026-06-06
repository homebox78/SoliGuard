/* ============================================================
   SoliGuard — Complete + Report preview
   ============================================================ */

function Complete({ state, dispatch }) {
  const d = state.completeData || { resolved: { masked: 0, quarantined: 0, deleted: 0 }, prevGrade: 'warn', newGrade: 'safe', handled: 0, remaining: [], scanned: 0 };
  const [report, setReport] = React.useState(false);
  const pg = GRADE_META[d.prevGrade], ng = GRADE_META[d.newGrade];
  const tiles = [
    { k: 'masked', label: '마스킹', icon: 'eyeOff', color: 'var(--info)', bg: 'var(--info-bg)', v: d.resolved.masked },
    { k: 'quarantined', label: '격리', icon: 'lock', color: 'var(--brand)', bg: 'var(--pink-50)', v: d.resolved.quarantined },
    { k: 'deleted', label: '완전삭제', icon: 'trash', color: 'var(--danger)', bg: 'var(--danger-bg)', v: d.resolved.deleted },
  ];
  return (
    <div className="view" style={{ height: '100%', overflowY: 'auto', display: 'grid', placeItems: 'center', padding: '32px' }}>
      <div style={{ width: '100%', maxWidth: 680 }}>
        <div style={{ textAlign: 'center', marginBottom: 26 }}>
          <div className="pop-in" style={{ width: 84, height: 84, borderRadius: '50%', background: 'var(--safe-bg)', color: 'var(--safe)', display: 'grid', placeItems: 'center', margin: '0 auto 18px' }}>
            <Icon name="checkCircle" size={46} stroke={2} />
          </div>
          <h1 style={{ margin: 0, fontSize: 26, fontWeight: 800, letterSpacing: '-.02em' }}>점검 완료</h1>
          <p style={{ color: 'var(--text-2)', fontSize: 14, marginTop: 8 }}>
            {d.handled > 0 ? <>선택한 <b>{d.handled}건</b>을 안전하게 처리했어요.</> : '점검을 마쳤어요.'}
          </p>
        </div>

        {/* result tiles */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 14, marginBottom: 16 }}>
          {tiles.map(t => (
            <div key={t.k} className="card" style={{ padding: '18px 16px', textAlign: 'center' }}>
              <div style={{ width: 38, height: 38, borderRadius: 10, background: t.bg, color: t.color, display: 'grid', placeItems: 'center', margin: '0 auto 10px' }}>
                <Icon name={t.icon} size={19} />
              </div>
              <CountUpNum target={t.v} style={{ fontSize: 30, fontWeight: 800, fontFamily: 'var(--mono)', color: t.v ? t.color : 'var(--text-3)' }} />
              <div style={{ fontSize: 12.5, color: 'var(--text-2)', fontWeight: 600, marginTop: 2 }}>{t.label}</div>
            </div>
          ))}
        </div>

        {/* grade improvement */}
        <div className="card" style={{ padding: '18px 24px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 22, marginBottom: 16 }}>
          <div style={{ textAlign: 'center', opacity: .65 }}>
            <div style={{ fontSize: 11.5, color: 'var(--text-3)', fontWeight: 700, marginBottom: 6 }}>점검 전</div>
            <span className={'sev ' + (d.prevGrade === 'danger' ? 'sev-high' : d.prevGrade === 'warn' ? 'sev-medium' : 'sev-low')} style={{ fontSize: 14, padding: '6px 14px' }}><span className="dot" />{pg.label}</span>
          </div>
          <Icon name="chevR" size={26} style={{ color: 'var(--text-3)' }} />
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 11.5, color: 'var(--text-3)', fontWeight: 700, marginBottom: 6 }}>점검 후</div>
            <span className={'sev ' + (d.newGrade === 'danger' ? 'sev-high' : d.newGrade === 'warn' ? 'sev-medium' : 'sev-low')} style={{ fontSize: 14, padding: '6px 14px', transform: 'scale(1.06)' }}><span className="dot" />{ng.label}</span>
          </div>
        </div>

        {/* report card */}
        <div className="card" style={{ padding: 20, display: 'flex', alignItems: 'center', gap: 16, marginBottom: 22, background: 'var(--surface-2)' }}>
          <div style={{ width: 50, height: 50, borderRadius: 12, background: 'var(--brand)', color: '#fff', display: 'grid', placeItems: 'center', flex: 'none' }}>
            <Icon name="fileText" size={24} />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 800, fontSize: 15 }}>점검 진단서 (PDF) 발급</div>
            <div style={{ color: 'var(--text-2)', fontSize: 12.5, marginTop: 2 }}>발주처 보안 감사·개인정보보호법 대응 증빙용 · 개인정보는 모두 마스킹됩니다</div>
          </div>
          <button className="btn btn-primary" onClick={() => setReport(true)}><Icon name="download" size={17} /> 리포트 저장</button>
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', gap: 10 }}>
          <button className="btn btn-ghost btn-lg" onClick={() => dispatch({ type: 'nav', v: 'quarantine' })}><Icon name="lock" size={17} /> 격리함 보기</button>
          <button className="btn btn-primary btn-lg" onClick={() => dispatch({ type: 'finishToHome' })}><Icon name="home" size={17} /> 홈으로</button>
        </div>
      </div>

      {report && <ReportModal state={state} d={d} onClose={() => setReport(false)} dispatch={dispatch} />}
    </div>
  );
}

function CountUpNum({ target, style }) {
  const v = useCountUp(target, 800, true);
  return <div style={style}>{v}</div>;
}

function ReportModal({ state, d, onClose, dispatch }) {
  const remaining = d.remaining || [];
  const now = new Date();
  const fmt = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
  // reconstruct detail from original dataset (masked)
  const dataset = DATASETS[state.role];
  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal" style={{ width: 560, maxHeight: '88%', display: 'flex', flexDirection: 'column' }} onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', alignItems: 'center', padding: '12px 14px 12px 18px', borderBottom: '1px solid var(--border)' }}>
          <span style={{ fontWeight: 700, fontSize: 13.5 }}>진단서 미리보기</span>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
            <button className="btn btn-primary btn-sm" onClick={() => { onClose(); dispatch({ type: 'toast', toast: { icon: 'download', tone: 'var(--brand)', msg: '진단서를 저장했어요 — soliguard_report.pdf' } }); }}><Icon name="download" size={14} /> 저장</button>
            <button className="btn btn-quiet btn-sm" onClick={onClose}><Icon name="x" size={15} /></button>
          </div>
        </div>
        <div className="scroll" style={{ padding: 22, background: '#EEF0F3' }}>
          {/* paper */}
          <div style={{ background: '#fff', borderRadius: 6, boxShadow: 'var(--sh-card)', overflow: 'hidden', fontSize: 12 }}>
            <div style={{ background: 'var(--brand)', color: '#fff', padding: '16px 22px', display: 'flex', alignItems: 'center', gap: 10 }}>
              <Icon name="shieldCheck" size={20} />
              <span style={{ fontWeight: 800, fontSize: 15 }}>솔리가드 개인정보 점검 진단서</span>
            </div>
            <div style={{ padding: '18px 22px' }}>
              <table style={{ width: '100%', fontSize: 12, color: 'var(--text-2)', borderCollapse: 'collapse', marginBottom: 14 }}>
                <tbody>
                  <tr><td style={{ padding: '3px 0', width: 90, color: 'var(--text-3)' }}>점검 일시</td><td>{fmt}</td><td style={{ width: 90, color: 'var(--text-3)' }}>직무 프로파일</td><td>{state.role}</td></tr>
                  <tr><td style={{ color: 'var(--text-3)' }}>검사 파일</td><td>{(d.scanned || 0).toLocaleString()}개</td><td style={{ color: 'var(--text-3)' }}>처리 건수</td><td>{d.handled}건</td></tr>
                </tbody>
              </table>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 14px', borderRadius: 8, background: GRADE_META[d.newGrade].bg, marginBottom: 16 }}>
                <span style={{ fontWeight: 800, fontSize: 14, color: GRADE_META[d.newGrade].color }}>종합 위험 등급: {GRADE_META[d.newGrade].label}</span>
                <span style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--text-2)' }}>마스킹 {d.resolved.masked} · 격리 {d.resolved.quarantined} · 삭제 {d.resolved.deleted}</span>
              </div>
              <div style={{ fontWeight: 700, fontSize: 12.5, marginBottom: 8, color: 'var(--text)' }}>검출 상세 <span style={{ color: 'var(--text-3)', fontWeight: 400 }}>(개인정보는 마스킹되어 표시됩니다)</span></div>
              {dataset.map((f, i) => (
                <div key={i} style={{ marginBottom: 10 }}>
                  <div style={{ fontWeight: 600, fontSize: 11.5, color: 'var(--text)' }}>📄 {f.path}\{f.file} <span style={{ color: 'var(--text-3)' }}>({f.findings.length}건)</span></div>
                  {f.findings.map(fd => (
                    <div key={fd.id} className="mono" style={{ fontSize: 11, color: SEV_META[fd.severity].color, paddingLeft: 12 }}>
                      [{SEV_META[fd.severity].label}] {fd.kind}: {fd.masked}{fd.line > 0 ? `  (line ${fd.line})` : ''}
                    </div>
                  ))}
                </div>
              ))}
              <div style={{ borderTop: '1px solid var(--border)', marginTop: 14, paddingTop: 12, fontSize: 10.5, color: 'var(--text-3)', lineHeight: 1.6 }}>
                ※ 본 진단서는 개인정보보호법 제21조·제24조·제29조 이행 점검 및 발주처 보안 감사 증빙용으로 활용됩니다.<br />
                ※ 본 점검은 사용자 PC 내에서 수행되었으며, 검출된 데이터는 외부로 전송되지 않았습니다.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { Complete });
