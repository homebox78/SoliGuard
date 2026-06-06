/* ============================================================
   SoliGuard — Results (3 layouts) + Confirm modal
   ============================================================ */

const ACTION_META = {
  mask:       { label: '마스킹', icon: 'eyeOff', past: '마스킹', tone: 'var(--info)',  bg: 'var(--info-bg)' },
  quarantine: { label: '격리',   icon: 'lock',   past: '격리',   tone: 'var(--brand)', bg: 'var(--pink-50)' },
  delete:     { label: '완전삭제', icon: 'trash', past: '삭제',   tone: 'var(--danger)', bg: 'var(--danger-bg)' },
};
const RES_KEY = { mask: 'masked', quarantine: 'quarantined', delete: 'deleted' };

function ctxFor(r) {
  const m = r.masked;
  const map = {
    '주민등록번호': `…고객 ${'홍**'} 님 / 주민등록번호 ${m} / 본인확인 완료…`,
    '신용카드번호': `…결제수단 등록  card_no=${m}  exp=**/**…`,
    'API키/시크릿': `api_key = "${m}"   # ⚠ 소스에 하드코딩됨`,
    'DB접속정보':   `spring.datasource.url=${m}`,
    '휴대전화번호': `…담당자 연락처 ${m} 로 안내 회신…`,
    '이메일':       `…회신: ${m} 으로 자료 송부 요청…`,
    '계좌번호':     `…환불 계좌 ${m} (○○은행)…`,
    '사업자등록번호': `…공급자 등록번호 ${m} 세금계산서…`,
    '신분증 이미지': `이미지 레이어에서 OCR로 검출된 신분증 정보 (${m})`,
    '실고객 샘플':   `…예시 데이터: ${m} (실제 고객 샘플로 추정)…`,
  };
  return map[r.kind] || `…${m}…`;
}

function RowActions({ r, onAct, compact }) {
  if (r.status === 'processing') return <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, color: 'var(--text-2)', fontSize: 12, fontWeight: 600 }}>
    <span style={{ width: 13, height: 13, border: '2px solid var(--border-strong)', borderTopColor: 'var(--brand)', borderRadius: '50%', animation: 'spin .7s linear infinite' }} /> 처리 중…</span>;
  return (
    <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
      <button className="btn btn-ghost btn-sm" title="마스킹" onClick={(e) => { e.stopPropagation(); onAct([r.uid], 'mask'); }}><Icon name="eyeOff" size={14} />{!compact && '마스킹'}</button>
      <button className="btn btn-ghost btn-sm" title="격리" onClick={(e) => { e.stopPropagation(); onAct([r.uid], 'quarantine'); }}><Icon name="lock" size={14} />{!compact && '격리'}</button>
      <button className="btn btn-ghost btn-sm" title="완전삭제" style={{ color: 'var(--danger)', borderColor: 'var(--danger-line)' }} onClick={(e) => { e.stopPropagation(); onAct([r.uid], 'delete'); }}><Icon name="trash" size={14} /></button>
    </div>
  );
}

function Results({ state, dispatch }) {
  const roles = state.roles;
  const initial = React.useMemo(() => flattenFindings(mergeDataset(roles)).map(r => ({ ...r, uid: r.id, status: 'idle' })), [roles]);
  const [rows, setRows] = React.useState(initial);
  const [resolved, setResolved] = React.useState({ masked: 0, quarantined: 0, deleted: 0 });
  const [sel, setSel] = React.useState(() => new Set());
  const [layout, setLayout] = React.useState('table');
  const [fSev, setFSev] = React.useState(() => new Set());
  const [fFile, setFFile] = React.useState(null);
  const [previewId, setPreviewId] = React.useState(initial[0]?.uid);
  const [confirm, setConfirm] = React.useState(null);
  const [open, setOpen] = React.useState(() => new Set(Array.from(new Set(initial.map(r => r.file)))));

  const discovered = initial.length;
  const counts = countBySeverity(rows);

  const visible = rows.filter(r => (fSev.size === 0 || fSev.has(r.severity)) && (!fFile || r.file === fFile));
  const files = Array.from(new Set(rows.map(r => r.file)));
  const preview = rows.find(r => r.uid === previewId) || visible[0];

  function perform(ids, action) {
    const items = rows.filter(r => ids.includes(r.uid));
    if (!items.length) return;
    setRows(rs => rs.map(r => ids.includes(r.uid) ? { ...r, status: 'processing', action } : r));
    setSel(new Set());
    setTimeout(() => {
      setRows(rs => rs.map(r => ids.includes(r.uid) ? { ...r, status: 'out' } : r));
      setResolved(x => ({ ...x, [RES_KEY[action]]: x[RES_KEY[action]] + items.length }));
      if (action === 'quarantine') dispatch({ type: 'quarantineAdd', items: items.map(i => ({ ...i, action, when: '방금' })) });
      dispatch({ type: 'toast', toast: {
        icon: ACTION_META[action].icon,
        tone: ACTION_META[action].tone,
        msg: `${items.length}건을 ${ACTION_META[action].past} 처리했어요`,
        undo: () => { setRows(rs => rs.map(r => ids.includes(r.uid) ? { ...r, status: 'idle', action: undefined } : r));
          setResolved(x => ({ ...x, [RES_KEY[action]]: Math.max(0, x[RES_KEY[action]] - items.length) }));
          if (action === 'quarantine') dispatch({ type: 'quarantineRemove', ids });
        }
      }});
      setTimeout(() => setRows(rs => rs.filter(r => !(ids.includes(r.uid) && r.status === 'out'))), 420);
    }, 720);
  }
  function act(ids, action) {
    if (action === 'delete') { setConfirm({ ids }); return; }
    perform(ids, action);
  }
  function falsePositive(uid) {
    setRows(rs => rs.filter(r => r.uid !== uid));
    dispatch({ type: 'toast', toast: { icon: 'check', tone: 'var(--safe)', msg: '오탐으로 표시했어요 — 다음 점검부터 제외됩니다' } });
  }
  function toggleSel(uid) { setSel(s => { const n = new Set(s); n.has(uid) ? n.delete(uid) : n.add(uid); return n; }); }
  function selAll() { setSel(s => s.size === visible.length ? new Set() : new Set(visible.map(r => r.uid))); }

  const allDone = rows.length === 0;
  const layoutOpts = [
    { value: 'table', label: '테이블', icon: 'list' },
    { value: 'group', label: '그룹', icon: 'layers' },
    { value: 'cards', label: '카드', icon: 'grid' },
  ];

  return (
    <div className="view" style={{ height: '100%', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      {/* header */}
      <div style={{ padding: '22px 32px 16px', borderBottom: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 14 }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <button className="btn btn-quiet btn-sm" style={{ marginBottom: 6, paddingLeft: 6 }} onClick={() => dispatch({ type: 'nav', v: 'dashboard' })}>
              <Icon name="chevL" size={15} /> 대시보드
            </button>
            <h1 style={{ margin: 0, fontSize: 20, fontWeight: 800, letterSpacing: '-.02em', whiteSpace: 'nowrap' }}>
              점검 결과 — 위험 <span style={{ color: 'var(--danger)' }}>{discovered}건</span> 발견
            </h1>
            <div style={{ color: 'var(--text-2)', fontSize: 13, marginTop: 4 }}>
              미리보기는 항상 마스킹된 형태로만 표시됩니다 · 남은 항목 {rows.length}건
              {(resolved.masked + resolved.quarantined + resolved.deleted) > 0 && <span> · 처리 {resolved.masked + resolved.quarantined + resolved.deleted}건</span>}
            </div>
          </div>
          <Segmented value={layout} options={layoutOpts} onChange={setLayout} />
          <button className="btn btn-primary" onClick={() => dispatch({ type: 'goComplete', payload: { resolved, discovered, roles, remaining: rows } })}>
            <Icon name="checkCircle" size={17} /> 완료 · 리포트
          </button>
        </div>
      </div>

      {/* body */}
      <div style={{ flex: 1, minHeight: 0, display: 'flex' }}>
        {layout === 'table' && (
          <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
            <FilterBar rows={rows} fSev={fSev} setFSev={setFSev} fFile={fFile} setFFile={setFFile} files={files} />
            <div style={{ flex: 1, minHeight: 0, display: 'flex' }}>
              <div className="scroll" style={{ flex: 1, minWidth: 0, padding: '12px 16px' }}>
                <TableHeadRow visible={visible} sel={sel} selAll={selAll} />
                <div>
                  {visible.map(r => (
                    <TableRow key={r.uid} r={r} sel={sel.has(r.uid)} active={preview && preview.uid === r.uid}
                      onSel={() => toggleSel(r.uid)} onAct={act} onClick={() => setPreviewId(r.uid)} />
                  ))}
                  {allDone && <EmptyResolved />}
                </div>
              </div>
              <PreviewPanel r={preview} onAct={act} onFP={falsePositive} />
            </div>
          </div>
        )}

        {layout === 'group' && (
          <div className="scroll" style={{ flex: 1, padding: '18px 32px' }}>
            {files.map(file => {
              const grp = rows.filter(r => r.file === file);
              if (!grp.length) return null;
              const c = countBySeverity(grp);
              const top = c.high ? 'high' : c.medium ? 'medium' : 'low';
              const isOpen = open.has(file);
              return (
                <div key={file} className="card" style={{ marginBottom: 12, overflow: 'hidden' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '14px 16px', cursor: 'pointer' }}
                    onClick={() => setOpen(o => { const n = new Set(o); n.has(file) ? n.delete(file) : n.add(file); return n; })}>
                    <Icon name={isOpen ? 'chevD' : 'chevR'} size={16} style={{ color: 'var(--text-3)' }} />
                    <Icon name={grp[0].fileIcon} size={18} style={{ color: 'var(--brand)' }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 700, fontSize: 13.5 }}>{file}</div>
                      <div className="mono" style={{ fontSize: 11.5, color: 'var(--text-3)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{grp[0].path}</div>
                    </div>
                    <SevTag severity={top} />
                    <span style={{ fontSize: 12.5, color: 'var(--text-2)', fontWeight: 700, width: 42, textAlign: 'right' }}>{grp.length}건</span>
                    <div style={{ display: 'flex', gap: 6 }} onClick={e => e.stopPropagation()}>
                      <button className="btn btn-ghost btn-sm" onClick={() => act(grp.map(g => g.uid), 'quarantine')}><Icon name="lock" size={13} /> 전체 격리</button>
                      <button className="btn btn-ghost btn-sm" style={{ color: 'var(--danger)', borderColor: 'var(--danger-line)' }} onClick={() => act(grp.map(g => g.uid), 'delete')}><Icon name="trash" size={13} /></button>
                    </div>
                  </div>
                  {isOpen && <div style={{ borderTop: '1px solid var(--border)' }}>
                    {grp.map(r => (
                      <div key={r.uid} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 16px 10px 44px', borderTop: '1px solid var(--surface-alt)',
                        opacity: r.status === 'out' ? 0 : 1, transition: 'opacity .35s' }}>
                        <Icon name={KIND_ICON[r.kind] || 'fileText'} size={15} style={{ color: 'var(--text-3)' }} />
                        <span style={{ fontSize: 13, fontWeight: 600, minWidth: 130 }}>{r.kind}</span>
                        <span className="mono" style={{ fontSize: 12.5, color: 'var(--text-2)', flex: 1 }}>{r.masked}</span>
                        {r.line > 0 && <span className="mono" style={{ fontSize: 11, color: 'var(--text-3)' }}>line {r.line}</span>}
                        <SevTag severity={r.severity} withDot={false} />
                        <RowActions r={r} onAct={act} compact />
                      </div>
                    ))}
                  </div>}
                </div>
              );
            })}
            {allDone && <EmptyResolved />}
          </div>
        )}

        {layout === 'cards' && (
          <div className="scroll" style={{ flex: 1, padding: '18px 32px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 16 }}>
              {['high', 'medium', 'low'].map(sev => {
                const grp = rows.filter(r => r.severity === sev);
                const m = SEV_META[sev];
                return (
                  <div key={sev}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                      <SevTag severity={sev} />
                      <span style={{ fontSize: 12.5, color: 'var(--text-3)', fontWeight: 600 }}>{grp.length}건</span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                      {grp.map(r => (
                        <div key={r.uid} className="card" style={{ padding: 14, borderLeft: `3px solid ${m.color}`,
                          opacity: r.status === 'out' ? 0 : 1, transform: r.status === 'out' ? 'translateX(12px)' : 'none', transition: 'all .35s' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                            <Icon name={KIND_ICON[r.kind] || 'fileText'} size={15} style={{ color: m.color }} />
                            <span style={{ fontWeight: 700, fontSize: 13 }}>{r.kind}</span>
                          </div>
                          <div className="mono" style={{ fontSize: 13, color: 'var(--text)', marginBottom: 6 }}>{r.masked}</div>
                          <div className="mono" style={{ fontSize: 11, color: 'var(--text-3)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', marginBottom: 10 }}>{r.file}</div>
                          <RowActions r={r} onAct={act} compact />
                        </div>
                      ))}
                      {grp.length === 0 && <div style={{ color: 'var(--text-3)', fontSize: 12.5, padding: '8px 2px' }}>해당 없음</div>}
                    </div>
                  </div>
                );
              })}
            </div>
            {allDone && <EmptyResolved />}
          </div>
        )}
      </div>

      {/* bulk action bar */}
      {sel.size > 0 && (
        <div style={{ position: 'absolute', bottom: 22, left: '50%', transform: 'translateX(-50%)', zIndex: 40,
          background: '#fff', border: '1px solid var(--border-strong)', borderRadius: 14, boxShadow: 'var(--sh-pop)',
          display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px 10px 18px', animation: 'fadeUp .2s ease' }}>
          <span style={{ fontSize: 13.5, fontWeight: 700 }}>선택 <span style={{ color: 'var(--brand)' }}>{sel.size}건</span></span>
          <span style={{ width: 1, height: 22, background: 'var(--border)' }} />
          <button className="btn btn-ghost btn-sm" onClick={() => act([...sel], 'mask')}><Icon name="eyeOff" size={14} /> 마스킹</button>
          <button className="btn btn-ghost btn-sm" onClick={() => act([...sel], 'quarantine')}><Icon name="lock" size={14} /> 격리</button>
          <button className="btn btn-danger btn-sm" onClick={() => act([...sel], 'delete')}><Icon name="trash" size={14} /> 완전삭제</button>
          <button className="btn btn-quiet btn-sm" onClick={() => setSel(new Set())}><Icon name="x" size={14} /></button>
        </div>
      )}

      {confirm && <ConfirmModal ids={confirm.ids} rows={rows} onClose={() => setConfirm(null)}
        onQuarantine={() => { const ids = confirm.ids; setConfirm(null); perform(ids, 'quarantine'); }}
        onDelete={() => { const ids = confirm.ids; setConfirm(null); perform(ids, 'delete'); }} />}
    </div>
  );
}

function TableHeadRow({ visible, sel, selAll }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '6px 12px 10px', fontSize: 11.5, color: 'var(--text-3)', fontWeight: 700, letterSpacing: '.02em' }}>
      <button onClick={selAll} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, display: 'grid', placeItems: 'center' }}>
        <Check on={visible.length > 0 && sel.size === visible.length} />
      </button>
      <span style={{ width: 40 }}>위험도</span>
      <span style={{ flex: 1 }}>파일 · 검출 항목</span>
      <span style={{ width: 100, textAlign: 'right' }}>조치</span>
    </div>
  );
}

function TableRow({ r, sel, active, onSel, onAct, onClick }) {
  return (
    <div onClick={onClick} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px', borderRadius: 10, cursor: 'pointer',
      background: active ? 'var(--row-selected)' : sel ? 'var(--pink-50)' : 'transparent',
      opacity: r.status === 'out' ? 0 : 1, transform: r.status === 'out' ? 'translateX(14px)' : 'none',
      transition: 'opacity .38s, transform .38s, background .12s',
      borderBottom: '1px solid var(--surface-alt)' }}
      onMouseEnter={e => { if (!active && !sel) e.currentTarget.style.background = 'var(--row-hover)'; }}
      onMouseLeave={e => { if (!active && !sel) e.currentTarget.style.background = 'transparent'; }}>
      <button onClick={e => { e.stopPropagation(); onSel(); }} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}><Check on={sel} /></button>
      <span style={{ width: 40 }}><SevTag severity={r.severity} withDot={false} /></span>
      <span style={{ flex: 1, minWidth: 0 }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: 7, minWidth: 0 }}>
          <Icon name={r.fileIcon} size={15} style={{ color: 'var(--text-3)', flex: 'none' }} />
          <span style={{ fontSize: 13, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{r.file}</span>
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: 5, minWidth: 0, marginTop: 1 }}>
          <Icon name={KIND_ICON[r.kind] || 'fileText'} size={11} style={{ color: SEV_META[r.severity].color, flex: 'none' }} />
          <span style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--text-2)', flex: 'none' }}>{r.kind}</span>
          <span className="mono" style={{ fontSize: 10.5, color: 'var(--text-3)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>· {r.path}{r.line > 0 ? ` · line ${r.line}` : ''}</span>
        </span>
      </span>
      <span style={{ width: 100 }}><RowActions r={r} onAct={onAct} compact /></span>
    </div>
  );
}

function FilterBar({ rows, fSev, setFSev, fFile, setFFile, files }) {
  const c = countBySeverity(rows);
  const sevs = [['high', c.high], ['medium', c.medium], ['low', c.low]];
  const toggle = (s) => setFSev(p => { const n = new Set(p); n.has(s) ? n.delete(s) : n.add(s); return n; });
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '11px 16px', borderBottom: '1px solid var(--border)', flexWrap: 'wrap' }}>
      <span style={{ fontSize: 11.5, fontWeight: 700, color: 'var(--text-3)', letterSpacing: '.04em' }}>위험도</span>
      {sevs.map(([s, n]) => {
        const m = SEV_META[s]; const on = fSev.has(s);
        return (
          <button key={s} onClick={() => toggle(s)} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '5px 11px', borderRadius: 999, cursor: 'pointer', fontSize: 12, fontWeight: 700, whiteSpace: 'nowrap',
            border: '1px solid ' + (on ? m.color : 'var(--border)'), background: on ? m.color : '#fff', color: on ? '#fff' : 'var(--text-2)' }}>
            <span style={{ width: 7, height: 7, borderRadius: '50%', background: on ? '#fff' : m.color }} />{m.label} {n}
          </button>
        );
      })}
      <span style={{ width: 1, height: 20, background: 'var(--border)', margin: '0 4px' }} />
      <Icon name="filter" size={14} style={{ color: 'var(--text-3)' }} />
      <select value={fFile || ''} onChange={e => setFFile(e.target.value || null)} style={{ height: 30, borderRadius: 8, border: '1px solid var(--border-strong)', padding: '0 10px', fontSize: 12.5, fontFamily: 'var(--font)', fontWeight: 600, color: 'var(--text)', background: '#fff', cursor: 'pointer', maxWidth: 220 }}>
        <option value="">전체 파일</option>
        {files.map(f => <option key={f} value={f}>{f}</option>)}
      </select>
      <span style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--text-3)', fontWeight: 600 }}>{rows.length}건</span>
    </div>
  );
}

function PreviewPanel({ r, onAct, onFP }) {
  if (!r) return <div style={{ width: 248, flex: 'none', borderLeft: '1px solid var(--border)' }} />;
  return (
    <div style={{ width: 248, flex: 'none', borderLeft: '1px solid var(--border)', padding: '18px 16px', overflowY: 'auto', background: 'var(--surface-2)' }}>
      <div style={{ fontSize: 11.5, fontWeight: 700, color: 'var(--text-3)', letterSpacing: '.06em', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 7 }}>
        <Icon name="eyeOff" size={14} /> 마스킹 미리보기
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 4 }}>
        <Icon name={r.fileIcon} size={18} style={{ color: 'var(--brand)' }} />
        <span style={{ fontWeight: 700, fontSize: 14 }}>{r.file}</span>
      </div>
      <div className="mono" style={{ fontSize: 11.5, color: 'var(--text-3)', marginBottom: 16, wordBreak: 'break-all' }}>{r.path}{r.line > 0 ? `  ·  line ${r.line}` : ''}</div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <Icon name={KIND_ICON[r.kind] || 'fileText'} size={16} style={{ color: SEV_META[r.severity].color }} />
        <span style={{ fontWeight: 700, fontSize: 13.5 }}>{r.kind}</span>
        <SevTag severity={r.severity} />
      </div>

      <div className="mono" style={{ fontSize: 22, fontWeight: 700, letterSpacing: '.02em', padding: '14px 16px', borderRadius: 12, background: '#fff', border: '1px solid var(--border)', marginBottom: 14, textAlign: 'center' }}>{r.masked}</div>

      <div style={{ fontSize: 11.5, fontWeight: 700, color: 'var(--text-3)', marginBottom: 7 }}>검출 위치 (마스킹됨)</div>
      <div className="mono" style={{ fontSize: 12, lineHeight: 1.7, color: 'var(--text-2)', padding: '12px 14px', borderRadius: 10, background: '#14161C', color: '#cfd3da', marginBottom: 18, wordBreak: 'break-word' }}>{ctxFor(r)}</div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <button className="btn btn-primary" onClick={() => onAct([r.uid], 'mask')}><Icon name="eyeOff" size={16} /> 마스킹</button>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-ghost" style={{ flex: 1 }} onClick={() => onAct([r.uid], 'quarantine')}><Icon name="lock" size={15} /> 격리</button>
          <button className="btn btn-ghost" style={{ flex: 1, color: 'var(--danger)', borderColor: 'var(--danger-line)' }} onClick={() => onAct([r.uid], 'delete')}><Icon name="trash" size={15} /> 삭제</button>
        </div>
        <button className="btn btn-quiet btn-sm" style={{ marginTop: 2 }} onClick={() => onFP(r.uid)}><Icon name="check" size={14} /> 이건 오탐이에요</button>
      </div>
    </div>
  );
}

function EmptyResolved() {
  return (
    <div className="fade-up" style={{ textAlign: 'center', padding: '60px 20px' }}>
      <div style={{ width: 76, height: 76, borderRadius: '50%', background: 'var(--safe-bg)', color: 'var(--safe)', display: 'grid', placeItems: 'center', margin: '0 auto 18px' }}>
        <Icon name="checkCircle" size={40} stroke={2} />
      </div>
      <div style={{ fontSize: 18, fontWeight: 800 }}>모든 항목을 처리했어요</div>
      <div style={{ color: 'var(--text-2)', fontSize: 13.5, marginTop: 6 }}>“점검 완료 · 리포트”를 눌러 진단서를 발급하세요.</div>
    </div>
  );
}

function ConfirmModal({ ids, rows, onClose, onQuarantine, onDelete }) {
  const [typed, setTyped] = React.useState('');
  const items = rows.filter(r => ids.includes(r.uid));
  const fileSet = Array.from(new Set(items.map(i => i.file)));
  const ok = typed.trim() === '삭제';
  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div style={{ padding: '22px 24px 0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 11, marginBottom: 14 }}>
            <span style={{ width: 40, height: 40, borderRadius: 11, background: 'var(--danger-bg)', color: 'var(--danger)', display: 'grid', placeItems: 'center', flex: 'none' }}>
              <Icon name="alert" size={22} />
            </span>
            <div>
              <div style={{ fontWeight: 800, fontSize: 17 }}>완전삭제 확인</div>
              <div style={{ color: 'var(--text-2)', fontSize: 12.5 }}>이 작업은 되돌릴 수 없습니다</div>
            </div>
          </div>
          <p style={{ fontSize: 13.5, color: 'var(--text)', lineHeight: 1.6, margin: '0 0 14px' }}>
            선택한 <b>{items.length}건</b>{fileSet.length > 1 ? ` (${fileSet.length}개 파일)` : ''}을 복구 불가능하게 영구 삭제합니다(덮어쓰기 삭제).
          </p>
          <div style={{ maxHeight: 120, overflowY: 'auto', borderRadius: 10, border: '1px solid var(--border)', padding: '6px 0', marginBottom: 14 }}>
            {items.slice(0, 8).map(i => (
              <div key={i.uid} style={{ display: 'flex', alignItems: 'center', gap: 9, padding: '6px 14px', fontSize: 12.5 }}>
                <Icon name={i.fileIcon} size={15} style={{ color: 'var(--text-3)' }} />
                <span style={{ flex: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{i.file}</span>
                <span style={{ color: 'var(--text-3)' }}>{i.kind}</span>
              </div>
            ))}
            {items.length > 8 && <div style={{ padding: '4px 14px', fontSize: 12, color: 'var(--text-3)' }}>외 {items.length - 8}건…</div>}
          </div>
          <div className="trust" style={{ marginBottom: 16 }}>
            <Icon name="shield" size={16} style={{ marginTop: 1, flex: 'none' }} />
            <span><b>권장</b> — 먼저 [격리]로 보관 후 검토하세요. 격리본은 언제든 복원할 수 있습니다.</span>
          </div>
          <label style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--text-2)' }}>확인을 위해 <b style={{ color: 'var(--danger)' }}>삭제</b>를 입력하세요</label>
          <input autoFocus value={typed} onChange={e => setTyped(e.target.value)} placeholder="삭제"
            style={{ width: '100%', marginTop: 8, height: 42, borderRadius: 10, border: '1.5px solid ' + (ok ? 'var(--danger)' : 'var(--border-strong)'), padding: '0 14px', fontSize: 14, outline: 'none', fontFamily: 'var(--font)' }} />
        </div>
        <div style={{ display: 'flex', gap: 10, padding: '18px 24px 22px' }}>
          <button className="btn btn-quiet" onClick={onClose}>취소</button>
          <button className="btn btn-ghost" style={{ marginLeft: 'auto' }} onClick={onQuarantine}><Icon name="lock" size={15} /> 격리로 변경</button>
          <button className="btn btn-danger" disabled={!ok} onClick={onDelete}><Icon name="trash" size={15} /> 영구 삭제</button>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { Results });
