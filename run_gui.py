"""PyInstaller 단일 exe 진입점 — 설치 마법사 + GUI + 백그라운드 에이전트 통합.

onefile 빌드(exe 하나)에서 SoliGuard.exe 가 모든 역할을 담당한다.
  - `--once`/`--agent` → 무인 스캔 에이전트(작업 스케줄러가 호출)
  - 첫 실행(설치 마커 없음) 또는 `--setup` → 설치 마법사 → 완료 후 트레이 앱
  - 그 외 → 트레이 앱(상주). 앱은 config 가 없으면 온보딩을 안내한다.

(soliguard/app.py 를 직접 최상위 스크립트로 실행하면 부모 패키지가 없어
 `from .config import ...` 상대 임포트가 실패하므로, 이 런처에서 패키지로 임포트한다.)
"""

import sys

_AGENT_FLAGS = {"--once", "--agent"}

if __name__ == "__main__":
    argv = sys.argv[1:]

    if _AGENT_FLAGS & set(argv):
        from soliguard.scheduler import run_agent

        sys.exit(run_agent(argv))

    from soliguard.config import CONFIG_DIR

    install_marker = CONFIG_DIR / ".installed"

    if "--silent" in argv:
        # 무인 설치(IT 일괄 배포·테스트용): UI 없이 기본 위치에 설치만 수행.
        from soliguard.installer import default_install_dir, perform_install

        exe = perform_install(
            default_install_dir(),
            {"desktop": True, "startmenu": True, "autoscan": True, "ocr": True},
        )
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        install_marker.write_text("1", encoding="utf-8")
        print(f"installed: {exe}")
        sys.exit(0)

    if "--setup" in argv or not install_marker.exists():
        from soliguard.installer import main as installer_main

        sys.exit(installer_main())

    from soliguard.app import main

    sys.exit(main())
