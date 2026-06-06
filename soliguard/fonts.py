"""Pretendard 폰트 로딩 - Qt에 직접 등록해 앱 전체 폰트를 통일한다.

Windows에 Pretendard ttf가 설치돼 있어도 Qt가 자동 인식하지 못하는 경우가 있어
(QFontDatabase.families() 미노출), addApplicationFont 로 명시 등록한다.
"""

from __future__ import annotations

import os

FAMILY = "Pretendard"

# 등록 시도 경로(시스템/사용자). 여러 굵기를 등록해 weight 렌더링을 보장.
_WEIGHTS = ["Regular", "Medium", "SemiBold", "Bold", "Light", "ExtraBold"]
_DIRS = [
    "C:/Windows/Fonts",
    os.path.expandvars(r"%LOCALAPPDATA%/Microsoft/Windows/Fonts"),
    "/usr/share/fonts/truetype/pretendard",
]

_loaded = False


def load_fonts(app=None) -> str:
    """Pretendard 를 Qt 애플리케이션에 등록하고 기본 폰트로 설정. 패밀리명 반환.

    등록 실패(파일 없음) 시 시스템 기본 폰트 패밀리를 반환한다.
    """
    global _loaded
    from PySide6.QtGui import QFont, QFontDatabase

    family = FAMILY
    if not _loaded:
        added_any = False
        # 이미 시스템에 노출돼 있으면 그대로 사용
        if FAMILY in QFontDatabase.families():
            added_any = True
        else:
            for d in _DIRS:
                for wt in _WEIGHTS:
                    path = os.path.join(d, f"Pretendard-{wt}.ttf")
                    if os.path.exists(path):
                        fid = QFontDatabase.addApplicationFont(path)
                        fams = QFontDatabase.applicationFontFamilies(fid)
                        if fams:
                            family = fams[0]
                            added_any = True
        _loaded = True
        if not added_any:
            # 폴백: 등록 실패 시 시스템 기본 유지
            return app.font().family() if app is not None else family

    if app is not None:
        f = QFont(family, 10)
        f.setStyleStrategy(QFont.PreferAntialias)
        app.setFont(f)
    return family
