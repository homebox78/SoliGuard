"""PyInstaller GUI 진입점 — 패키지를 정상 임포트해 상대 임포트 문제를 피한다.

(soliguard/app.py 를 직접 최상위 스크립트로 실행하면 부모 패키지가 없어
 `from .config import ...` 상대 임포트가 실패하므로, 이 런처에서 패키지로 임포트한다.)
"""

import sys

from soliguard.app import main

if __name__ == "__main__":
    sys.exit(main())
