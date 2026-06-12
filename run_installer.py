"""PyInstaller 설치기 진입점 — 커스텀 크림슨 설치 마법사를 띄운다.

번들된 payload.zip(앱 본체)을 사용자가 고른 폴더로 풀어 실제 설치를 수행한다.
"""

import sys

from soliguard.installer import main

if __name__ == "__main__":
    sys.exit(main())
