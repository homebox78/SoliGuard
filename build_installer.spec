# PyInstaller 스펙 - 커스텀 설치기(단일 SoliGuardSetup.exe)
#
# 빌드 순서:
#   1) pyinstaller build_exe.spec                 → dist/SoliGuard/ (앱 본체)
#   2) python -c "import shutil; shutil.make_archive('build/payload','zip','dist/SoliGuard')"
#                                                  → build/payload.zip (앱 페이로드)
#   3) pyinstaller build_installer.spec           → dist/SoliGuardSetup.exe (설치기)
#
# 설치기는 payload.zip 을 번들로 품고, 실행 시 사용자가 고른 폴더로 풀어 설치한다.
block_cipher = None

datas = [
    ("build/payload.zip", "."),          # 앱 본체(설치 대상 페이로드)
    ("assets/fonts/*.ttf", "assets/fonts"),
    ("assets/*.svg", "assets"),
    ("assets/brand/*.png", "assets/brand"),
    ("assets/soliguard.ico", "assets"),
]

a = Analysis(["run_installer.py"], pathex=["."], datas=datas,
             hiddenimports=["PySide6"], cipher=block_cipher)
pyz = PYZ(a.pure)
# a.binaries/a.datas 를 EXE 에 직접 포함 → 단일 파일(onefile)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="SoliGuardSetup",
    console=False,
    icon="assets/soliguard.ico",
)
