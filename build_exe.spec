# PyInstaller 빌드 스펙 - 단일 exe(onefile). GUI + 백그라운드 에이전트 통합.
# 빌드:  pyinstaller build_exe.spec --distpath . --workpath build
#        (--distpath . → dist 폴더 없이 프로젝트 루트에 SoliGuard.exe 생성)
# 산출:  ./SoliGuard.exe  (이 파일 하나만 배포하면 됨)
#
# 동작: 인자 없이 실행하면 GUI, `--once` 인자로 실행하면 무인 스캔 에이전트.
#       작업 스케줄러는 SoliGuard.exe --once 를 주기 호출한다(scheduler.py 참고).
#
# 주의: 본 패키지는 flat 레이아웃(soliguard/)이므로 pathex 는 프로젝트 루트(".").
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

hidden = (
    collect_submodules("apscheduler")
    + collect_submodules("pdfplumber")
    + collect_submodules("cryptography")   # 격리(AES-256-GCM) — 지연 import 라 명시 필요
    + ["pytesseract", "openpyxl", "docx", "olefile", "reportlab",
       "psd_tools", "requests", "PySide6",
       "cryptography.hazmat.primitives.ciphers.aead"]
)

datas = collect_data_files("reportlab")
datas += [("assets/soliguard.ico", "assets")]
datas += [("assets/fonts/*.ttf", "assets/fonts")]   # 번들 Pretendard(배포 보장)
datas += [("assets/*.svg", "assets")]               # QSS 아이콘(체크/드롭다운 화살표)
datas += [("assets/brand/*.png", "assets/brand")]   # solideo 브랜드 로고
# OCR 데이터(kor) 번들 시:  datas += [("vendor/tesseract", "tesseract")]

a = Analysis(["run_gui.py"], pathex=["."],
             datas=datas, hiddenimports=hidden, cipher=block_cipher)
pyz = PYZ(a.pure)

# onefile: 모든 바이너리/데이터를 EXE 하나에 포함(COLLECT 미사용 → _internal 폴더 없음).
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="SoliGuard",
    console=False,
    icon="assets/soliguard.ico",
    upx=True,
    runtime_tmpdir=None,
)
