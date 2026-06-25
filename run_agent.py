"""PyInstaller 백그라운드 에이전트 진입점(--once 무인 스캔).

soliguard/scheduler.py 를 직접 실행하면 상대 임포트가 실패하므로 패키지로 임포트한다.
"""

import sys

from soliguard.scheduler import run_agent

if __name__ == "__main__":
    sys.exit(run_agent(sys.argv[1:]))
