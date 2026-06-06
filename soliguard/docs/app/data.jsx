/* ============================================================
   SoliGuard — icons, sample data, helpers
   ============================================================ */

/* ---- Lucide-style line icons (24x24 stroke) ---- */
const ICON_PATHS = {
  home: 'M3 9.5 12 3l9 6.5V20a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1z',
  shield: 'M12 22s8-3.6 8-9.5V5.3l-8-3-8 3v7.2C4 18.4 12 22 12 22z',
  shieldCheck: ['M12 22s8-3.6 8-9.5V5.3l-8-3-8 3v7.2C4 18.4 12 22 12 22z','m9 12 2 2 4-4'],
  search: ['M11 11m-8 0a8 8 0 1 0 16 0a8 8 0 1 0-16 0','m21 21-4.3-4.3'],
  lock: ['M5 11h14a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-8a1 1 0 0 1 1-1z','M8 11V7a4 4 0 0 1 8 0v4'],
  trash: ['M3 6h18','M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2','M19 6v13a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6','M10 11v6','M14 11v6'],
  eyeOff: ['M9.9 5.1A9.6 9.6 0 0 1 12 5c5 0 9 5 9 7a12 12 0 0 1-2.1 2.6','M6.6 6.6C3.8 8 2 11 2 12c1 2 5 7 10 7a9 9 0 0 0 3.4-.7','M3 3l18 18','M9.9 9.9a3 3 0 0 0 4.2 4.2'],
  fileText: ['M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z','M14 2v6h6','M9 13h6','M9 17h6','M9 9h1'],
  history: ['M3 12a9 9 0 1 0 3-6.7L3 8','M3 3v5h5','M12 7v5l3.5 2'],
  settings: ['M12.5 2h-1a2 2 0 0 0-2 2 1.7 1.7 0 0 1-.85 1.48l-.7.4a1.7 1.7 0 0 1-1.7 0l-.3-.16a2 2 0 0 0-2.73.73l-.5.87a2 2 0 0 0 .73 2.73l.3.18a1.7 1.7 0 0 1 .85 1.47v.8a1.7 1.7 0 0 1-.85 1.48l-.3.17a2 2 0 0 0-.73 2.73l.5.87a2 2 0 0 0 2.73.73l.3-.17a1.7 1.7 0 0 1 1.7 0l.7.4A1.7 1.7 0 0 1 9.5 20a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2 1.7 1.7 0 0 1 .85-1.48l.7-.4a1.7 1.7 0 0 1 1.7 0l.3.17a2 2 0 0 0 2.73-.73l.5-.87a2 2 0 0 0-.73-2.73l-.3-.17a1.7 1.7 0 0 1-.85-1.48v-.8a1.7 1.7 0 0 1 .85-1.47l.3-.18a2 2 0 0 0 .73-2.73l-.5-.87a2 2 0 0 0-2.73-.73l-.3.16a1.7 1.7 0 0 1-1.7 0l-.7-.4A1.7 1.7 0 0 1 14.5 4a2 2 0 0 0-2-2z','M12 12m-3 0a3 3 0 1 0 6 0a3 3 0 1 0-6 0'],
  folder: 'M4 5h4.5l2 2.2H20a1 1 0 0 1 1 1V19a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z',
  folderPlus: ['M4 5h4.5l2 2.2H20a1 1 0 0 1 1 1V19a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z','M12 12v5','M9.5 14.5h5'],
  chevR: 'm9 6 6 6-6 6',
  chevD: 'm6 9 6 6 6-6',
  chevL: 'm15 6-6 6 6 6',
  check: 'M20 6 9 17l-5-5',
  checkCircle: ['M22 11.1V12a10 10 0 1 1-5.9-9.1','m8.5 11.5 3 3 8-8'],
  x: ['M18 6 6 18','M6 6l12 12'],
  alert: ['m10.3 4 -8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.7-3l-8-14a2 2 0 0 0-3.4 0z','M12 9v4','M12 17h.01'],
  plus: ['M5 12h14','M12 5v14'],
  minus: 'M5 12h14',
  archive: ['M3 4h18v4H3z','M5 8v11a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8','M10 12h4'],
  clock: ['M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0-18 0','M12 7v5l3 2'],
  download: ['M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4','m7 10 5 5 5-5','M12 15V3'],
  pause: ['M9 4v16','M15 4v16'],
  stop: 'M6 6h12v12H6z',
  image: ['M3 5h18a0 0 0 0 1 0 0v14a0 0 0 0 1 0 0H3a0 0 0 0 1 0 0V5a0 0 0 0 1 0 0z','M8.5 11a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z','m21 16-5-5-7 7'],
  code: ['m16 18 6-6-6-6','m8 6-6 6 6 6'],
  key: ['M14.5 9.5a4.5 4.5 0 1 0-3.6 4.4L13 16h2v2h2v2h3v-3l-3.5-3.5a4.5 4.5 0 0 0 .9-3.5z'],
  database: ['M12 5m-8 0a8 3 0 1 0 16 0a8 3 0 1 0-16 0','M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5','M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6'],
  mail: ['M3 5h18a0 0 0 0 1 0 0v14a0 0 0 0 1 0 0H3a0 0 0 0 1 0 0V5a0 0 0 0 1 0 0z','m3 6 9 6 9-6'],
  phone: 'M21 16.4v2.5a2 2 0 0 1-2.2 2 19.6 19.6 0 0 1-8.5-3 19.3 19.3 0 0 1-6-6 19.6 19.6 0 0 1-3-8.6A2 2 0 0 1 3.3 3h2.5a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L7 10.6a16 16 0 0 0 6 6l1.1-1a2 2 0 0 1 2.1-.5c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z',
  card: ['M3 6h18a0 0 0 0 1 0 0v12a0 0 0 0 1 0 0H3a0 0 0 0 1 0 0V6a0 0 0 0 1 0 0z','M3 10h18'],
  user: ['M12 7m-4 0a4 4 0 1 0 8 0a4 4 0 1 0-8 0','M4 21a8 8 0 0 1 16 0'],
  users: ['M9 8m-3.5 0a3.5 3.5 0 1 0 7 0a3.5 3.5 0 1 0-7 0','M2 20a7 7 0 0 1 14 0','M16 4.5a3.5 3.5 0 0 1 0 7','M22 20a7 7 0 0 0-4-6.3'],
  filter: 'M3 4h18l-7 8v6l-4 2v-8z',
  rotate: ['M3 3v5h5','M3.5 8A9 9 0 1 1 5 14'],
  hardDrive: ['M5.4 5.1 2 12v6a1 1 0 0 0 1 1h18a1 1 0 0 0 1-1v-6l-3.4-6.9A2 2 0 0 0 16.8 4H7.2a2 2 0 0 0-1.8 1.1z','M2 12h20','M6 16h.01','M10 16h.01'],
  scan: ['M3 7V5a2 2 0 0 1 2-2h2','M17 3h2a2 2 0 0 1 2 2v2','M21 17v2a2 2 0 0 1-2 2h-2','M7 21H5a2 2 0 0 1-2-2v-2','M7 12h10'],
  bolt: 'M13 2 4 14h6l-1 8 9-12h-6z',
  layers: ['m12 2 9 5-9 5-9-5z','m3 12 9 5 9-5','m3 17 9 5 9-5'],
  grid: ['M3 3h7v7H3z','M14 3h7v7h-7z','M14 14h7v7h-7z','M3 14h7v7H3z'],
  list: ['M8 6h13','M8 12h13','M8 18h13','M3 6h.01','M3 12h.01','M3 18h.01'],
  more: ['M12 6h.01','M12 12h.01','M12 18h.01'],
  external: ['M15 3h6v6','M10 14 21 3','M19 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h6'],
  doc: ['M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z','M14 2v6h6'],
  sparkle: ['M12 3l1.6 4.6L18 9l-4.4 1.4L12 15l-1.6-4.6L6 9l4.4-1.4z','M19 14l.7 2 .7-2 .6 2','M5 4l.6 1.6L7 6'],
  refresh: ['M21 12a9 9 0 1 1-3-6.7','M21 4v4h-4'],
  cpu: ['M6 6h12v12H6z','M10 10h4v4h-4z','M9 2v2','M15 2v2','M9 20v2','M15 20v2','M2 9h2','M2 15h2','M20 9h2','M20 15h2'],
  drive: ['M4 5h16a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z','M7 9h6','M7 13h10','M16 9h.01'],
};

function Icon({ name, size = 20, stroke = 2, className = '', style = {} }) {
  const d = ICON_PATHS[name];
  const arr = Array.isArray(d) ? d : [d];
  return (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round" style={style}>
      {arr.map((p, i) => <path key={i} d={p} />)}
    </svg>
  );
}

/* ---- Roles ---- */
const ROLES = [
  { id: '개발자',   icon: 'code',     desc: '소스코드·설정파일 속 API키·DB접속정보' },
  { id: '디자이너', icon: 'image',    desc: '시안·PSD 이미지 속 신분증·계약서(OCR)' },
  { id: '기획자',   icon: 'fileText', desc: '산출물 문서 속 실고객 샘플' },
  { id: 'PM',       icon: 'layers',   desc: '프로젝트 문서·일정 산출물' },
  { id: '전산사무', icon: 'drive',    desc: '명부·정산 엑셀 속 개인정보' },
];

/* kind -> icon */
const KIND_ICON = {
  '주민등록번호': 'user', '신용카드번호': 'card', '사업자등록번호': 'fileText',
  '휴대전화번호': 'phone', '이메일': 'mail', '계좌번호': 'database',
  'API키/시크릿': 'key', 'DB접속정보': 'database', '여권번호': 'fileText',
  '신분증 이미지': 'image', '실고객 샘플': 'users',
};

/* ---- Findings per role. severity: high|medium|low ---- */
function mkFinding(id, kind, masked, severity, line) {
  return { id, kind, masked, severity, line, status: 'idle' };
}

const FILE_ICON = (name) => {
  if (/\.(png|jpe?g|psd|psb|bmp|tiff?)$/i.test(name)) return 'image';
  if (/\.(yml|yaml|env|json|py|js|java|sql|properties)$/i.test(name)) return 'code';
  if (/\.(hwp|hwpx|docx?)$/i.test(name)) return 'fileText';
  if (/\.(xlsx?|csv)$/i.test(name)) return 'database';
  return 'doc';
};

const DATASETS = {
  '개발자': [
    { file: '고객명단_운영추출.xlsx', path: 'C:\\Projects\\고객사A\\data', findings: [
      mkFinding('d1','주민등록번호','900101-2******','high',12),
      mkFinding('d2','주민등록번호','881215-1******','high',47),
      mkFinding('d3','휴대전화번호','010-****-1234','medium',12),
      mkFinding('d4','이메일','k***@clienta.co.kr','low',12),
    ]},
    { file: 'config.prod.yml', path: 'C:\\Projects\\고객사A\\src\\resources', findings: [
      mkFinding('d5','API키/시크릿','AKIA****************9xZqW2','high',8),
      mkFinding('d6','DB접속정보','jdbc:mysql://****@10.0.0.1','high',3),
    ]},
    { file: 'payment_test.log', path: 'C:\\Users\\me\\Downloads', findings: [
      mkFinding('d7','신용카드번호','4111-****-****-1111','high',204),
      mkFinding('d8','계좌번호','110-***-****56','medium',88),
    ]},
    { file: '회의록_0312.docx', path: 'C:\\Users\\me\\Desktop', findings: [
      mkFinding('d9','휴대전화번호','010-****-9921','medium',5),
      mkFinding('d10','이메일','lee***@clienta.co.kr','low',7),
    ]},
    { file: 'seed_dummy.sql', path: 'C:\\Projects\\고객사A\\db', findings: [
      mkFinding('d11','이메일','test***@example.com','low',31),
    ]},
  ],
  '디자이너': [
    { file: '시안_가입화면_신분증.png', path: 'C:\\Design\\시안\\고객사A', findings: [
      mkFinding('g1','신분증 이미지','주민번호(이미지) 90****','high',0),
      mkFinding('g2','주민등록번호','900101-2******','high',0),
    ]},
    { file: '메인배너_v3.psd', path: 'C:\\Design\\작업', findings: [
      mkFinding('g3','휴대전화번호','010-****-2210','medium',0),
      mkFinding('g4','이메일','sales***@clienta.co.kr','low',0),
    ]},
    { file: '계약서_스캔본.jpg', path: 'C:\\Users\\me\\Downloads', findings: [
      mkFinding('g5','신분증 이미지','계약서 스캔(이미지)','high',0),
      mkFinding('g6','사업자등록번호','220-**-***63','medium',0),
    ]},
    { file: '리플렛_초안.pdf', path: 'C:\\Design\\시안', findings: [
      mkFinding('g7','휴대전화번호','010-****-7788','medium',2),
    ]},
  ],
  '기획자': [
    { file: '요건정의서_v2.hwp', path: 'C:\\산출물\\고객사A', findings: [
      mkFinding('p1','실고객 샘플','홍** / 90****-2*','high',24),
      mkFinding('p2','휴대전화번호','010-****-1234','medium',24),
      mkFinding('p3','이메일','hong***@clienta.co.kr','low',26),
    ]},
    { file: '테스트시나리오.xlsx', path: 'C:\\산출물', findings: [
      mkFinding('p4','주민등록번호','881215-1******','high',58),
      mkFinding('p5','계좌번호','333-**-****01','medium',58),
    ]},
    { file: '회의록_0521.docx', path: 'C:\\Users\\me\\Desktop', findings: [
      mkFinding('p6','휴대전화번호','010-****-3030','medium',9),
      mkFinding('p7','이메일','pm***@clienta.co.kr','low',11),
    ]},
  ],
  'PM': [
    { file: '인력투입계획.xlsx', path: 'C:\\프로젝트\\고객사A', findings: [
      mkFinding('m1','주민등록번호','910303-1******','high',15),
      mkFinding('m2','휴대전화번호','010-****-4567','medium',15),
    ]},
    { file: '검수확인서.pdf', path: 'C:\\프로젝트\\고객사A\\산출', findings: [
      mkFinding('m3','사업자등록번호','220-**-***63','medium',3),
      mkFinding('m4','이메일','client***@clienta.co.kr','low',4),
    ]},
    { file: '주간보고_0603.docx', path: 'C:\\Users\\me\\Desktop', findings: [
      mkFinding('m5','휴대전화번호','010-****-8080','medium',6),
    ]},
  ],
  '전산사무': [
    { file: '직원명부_2026.xlsx', path: 'C:\\Documents\\인사', findings: [
      mkFinding('s1','주민등록번호','870707-2******','high',2),
      mkFinding('s2','주민등록번호','920912-1******','high',3),
      mkFinding('s3','휴대전화번호','010-****-1212','medium',2),
    ]},
    { file: '경비정산_5월.xlsx', path: 'C:\\Documents\\회계', findings: [
      mkFinding('s4','계좌번호','110-***-****78','medium',40),
      mkFinding('s5','신용카드번호','5555-****-****-4444','high',41),
    ]},
    { file: '거래처연락망.csv', path: 'C:\\Documents', findings: [
      mkFinding('s6','이메일','vendor***@partner.co.kr','low',12),
      mkFinding('s7','휴대전화번호','010-****-0099','medium',12),
    ]},
  ],
};

/* role default scan config */
const ROLE_CONFIG = {
  '개발자':   { folders: ['C:\\Users\\me\\Downloads','C:\\Users\\me\\Desktop','C:\\Projects\\고객사A'], kinds: ['주민등록번호','신용카드','전화/이메일','계좌번호','사업자번호','DB·API키'], ocr: false, exts: 'py, js, sql, yml, env, json, log, xlsx, docx, pdf' },
  '디자이너': { folders: ['C:\\Users\\me\\Downloads','C:\\Design\\시안','C:\\Design\\작업'], kinds: ['주민등록번호','신용카드','전화/이메일','이미지 속 정보(OCR)'], ocr: true, exts: 'psd, psb, xd, jpg, png, bmp, pdf, docx' },
  '기획자':   { folders: ['C:\\Users\\me\\Downloads','C:\\Users\\me\\Desktop','C:\\산출물'], kinds: ['주민등록번호','신용카드','전화/이메일','계좌번호','한글(hwp) 문서'], ocr: false, exts: 'hwp, hwpx, docx, xlsx, csv, pdf, txt' },
  'PM':       { folders: ['C:\\Users\\me\\Downloads','C:\\Users\\me\\Desktop','C:\\프로젝트'], kinds: ['주민등록번호','신용카드','전화/이메일','한글(hwp) 문서'], ocr: false, exts: 'hwp, hwpx, docx, xlsx, csv, pdf' },
  '전산사무': { folders: ['C:\\Users\\me\\Downloads','C:\\Documents'], kinds: ['주민등록번호','신용카드','전화/이메일','계좌번호'], ocr: false, exts: 'xlsx, csv, docx, hwp, pdf' },
};

const ALL_KINDS = ['주민등록번호','신용카드','전화/이메일','계좌번호','사업자번호','DB·API키','이미지 속 정보(OCR)','한글(hwp) 문서'];

/* flatten dataset to findings rows with file context */
function flattenFindings(dataset) {
  const rows = [];
  dataset.forEach((f, fi) => {
    f.findings.forEach(fd => rows.push({ ...fd, file: f.file, path: f.path, fileIcon: FILE_ICON(f.file) }));
  });
  return rows;
}
function countBySeverity(rows) {
  return rows.reduce((a, r) => (a[r.severity]++, a), { high: 0, medium: 0, low: 0 });
}

/* ---- multi-role merge ---- */
function mergeConfig(roles) {
  const folders = [], kinds = []; let ocr = false; const exts = [];
  (roles || []).forEach(r => {
    const c = ROLE_CONFIG[r]; if (!c) return;
    c.folders.forEach(f => { if (!folders.includes(f)) folders.push(f); });
    c.kinds.forEach(k => { if (!kinds.includes(k)) kinds.push(k); });
    ocr = ocr || c.ocr;
    c.exts.split(',').map(s => s.trim()).forEach(e => { if (!exts.includes(e)) exts.push(e); });
  });
  return { folders, kinds, ocr, exts: exts.join(', ') };
}
function mergeDataset(roles) {
  const out = []; (roles || []).forEach(r => (DATASETS[r] || []).forEach(d => out.push(d))); return out;
}
function rolesLabel(roles) {
  if (!roles || !roles.length) return '직무 미선택';
  if (roles.length === ROLES.length) return '전체 직무';
  if (roles.length === 1) return roles[0];
  return `${roles[0]} 외 ${roles.length - 1}`;
}
function rolesIcon(roles) { return (roles && roles.length === 1) ? (ROLES.find(r => r.id === roles[0])?.icon || 'user') : 'users'; }
function gradeOf(c) { return c.high > 0 ? 'danger' : c.medium > 0 ? 'warn' : 'safe'; }
const GRADE_META = {
  safe:   { label: '안전', color: 'var(--safe)',   bg: 'var(--safe-bg)',   ko: '안전합니다' },
  warn:   { label: '주의', color: 'var(--warn)',   bg: 'var(--warn-bg)',   ko: '주의가 필요해요' },
  danger: { label: '위험', color: 'var(--danger)', bg: 'var(--danger-bg)', ko: '즉시 조치가 필요해요' },
};
const SEV_META = {
  high:   { label: '높음', cls: 'sev-high',   color: 'var(--danger)' },
  medium: { label: '중간', cls: 'sev-medium', color: 'var(--warn)' },
  low:    { label: '낮음', cls: 'sev-low',    color: 'var(--safe)' },
};

Object.assign(window, {
  Icon, ICON_PATHS, ROLES, KIND_ICON, DATASETS, ROLE_CONFIG, ALL_KINDS,
  flattenFindings, countBySeverity, gradeOf, GRADE_META, SEV_META, FILE_ICON,
  mergeConfig, mergeDataset, rolesLabel, rolesIcon,
});
