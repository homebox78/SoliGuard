"""Pretendard 폰트 로딩 - 앱에 '번들된' ttf를 직접 등록해 어디서나 동일 적용.

근본 원칙(반복 누락 방지):
  - 시스템 설치 여부에 의존하지 않는다. assets/fonts 에 번들한 Pretendard ttf 를
    QFontDatabase.addApplicationFont 로 '항상' 등록하고, 그 패밀리를 앱 기본 폰트로
    설정한다. → 개발/배포(PyInstaller) 환경 모두에서 보장된다.
  - 검증은 요청 패밀리가 아니라 실제 등록 결과(applicationFontFamilies)로 한다.
"""

from __future__ import annotations

import sys
from pathlib import Path

FAMILY = "Pretendard"
_WEIGHTS = ("Regular", "Medium", "SemiBold", "Bold")
_loaded_family: str | None = None


def _font_dir() -> Path:
    # PyInstaller 로 묶이면 _MEIPASS 아래 assets/fonts 에 위치
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    d = base / "assets" / "fonts"
    if d.is_dir():
        return d
    # 패키지 기준 상위 경로 폴백
    return Path(__file__).resolve().parent.parent / "assets" / "fonts"


def load_fonts(app=None) -> str:
    """번들 Pretendard 를 등록하고 앱 기본 폰트로 설정. 등록된 패밀리명 반환."""
    global _loaded_family
    from PySide6.QtGui import QFont, QFontDatabase

    if _loaded_family is None:
        fam = None
        fdir = _font_dir()
        for wt in _WEIGHTS:
            p = fdir / f"Pretendard-{wt}.ttf"
            if p.exists():
                fid = QFontDatabase.addApplicationFont(str(p))
                fams = QFontDatabase.applicationFontFamilies(fid)
                if fams:
                    fam = fams[0]
        # 번들이 없으면 시스템 등록분 사용(최후 폴백)
        if fam is None and FAMILY in QFontDatabase.families():
            fam = FAMILY
        _loaded_family = fam or FAMILY

    if app is not None:
        f = QFont(_loaded_family, 10)
        f.setStyleStrategy(QFont.PreferAntialias)
        app.setFont(f)
        # 패밀리가 'Pretendard'가 아닐 수도 있으니 QSS도 함께 일치시키도록 노출
        app.setProperty("appFontFamily", _loaded_family)
    return _loaded_family
