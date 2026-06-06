# PyInstaller 빌드 스펙 - GUI 앱 + 백그라운드 에이전트.
# 빌드:  pyinstaller build_exe.spec
# 산출:  dist/SoliGuard/SoliGuard.exe(GUI), dist/SoliGuard/SoliGuardAgent.exe(에이전트)
#
# 주의: 본 패키지는 flat 레이아웃(soliguard/)이므로 pathex 는 프로젝트 루트(".").
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

hidden = (
    collect_submodules("apscheduler")
    + collect_submodules("pdfplumber")
    + ["pytesseract", "openpyxl", "docx", "olefile", "reportlab",
       "psd_tools", "requests", "PySide6"]
)

datas = collect_data_files("reportlab")
datas += [("assets/soliguard.ico", "assets")]
# OCR 데이터(kor) 번들 시:  datas += [("vendor/tesseract", "tesseract")]

# 1) GUI 앱 (app.py = 트레이 상주 진입점)
gui_a = Analysis(["soliguard/app.py"], pathex=["."],
                 datas=datas, hiddenimports=hidden, cipher=block_cipher)
gui_pyz = PYZ(gui_a.pure)
gui_exe = EXE(gui_pyz, gui_a.scripts, [], exclude_binaries=True,
              name="SoliGuard", console=False, icon="assets/soliguard.ico")

# 2) 백그라운드 에이전트 (scheduler.py, --once 로 1회 스캔)
agent_a = Analysis(["soliguard/scheduler.py"], pathex=["."],
                   datas=datas, hiddenimports=hidden, cipher=block_cipher)
agent_pyz = PYZ(agent_a.pure)
agent_exe = EXE(agent_pyz, agent_a.scripts, [], exclude_binaries=True,
                name="SoliGuardAgent", console=False, icon="assets/soliguard.ico")

coll = COLLECT(gui_exe, gui_a.binaries, gui_a.datas,
               agent_exe, agent_a.binaries, agent_a.datas,
               name="SoliGuard")
