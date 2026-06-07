"""아이콘/로고 유틸 - 흰색 라인 방패, 앱 아이콘, 실제 브랜드 로고 로딩.

- 방패: 파랑 이모지 대신 흰색 2px 외곽선으로 그린다(QPainter).
- 로고: 실제 첨부 로고 파일(assets/brand/)을 우선 사용, 없으면 None.
"""

from __future__ import annotations

from pathlib import Path

_ASSETS = Path(__file__).resolve().parent.parent / "assets"
_BRAND = _ASSETS / "brand"

CRIMSON = "#B0123F"

__all__ = ["shield_pixmap", "app_icon", "logo_pixmap", "line_icon", "ICON_PATHS"]

# Lucide 스타일 라인 아이콘 패스(시안 docs/app/data.jsx 포팅)
ICON_PATHS = {
    "home": ["M3 9.5 12 3l9 6.5V20a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1z"],
    "shield": ["M12 22s8-3.6 8-9.5V5.3l-8-3-8 3v7.2C4 18.4 12 22 12 22z"],
    "shieldCheck": ["M12 22s8-3.6 8-9.5V5.3l-8-3-8 3v7.2C4 18.4 12 22 12 22z", "m9 12 2 2 4-4"],
    "search": ["M11 11m-8 0a8 8 0 1 0 16 0a8 8 0 1 0-16 0", "m21 21-4.3-4.3"],
    "lock": ["M5 11h14a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-8a1 1 0 0 1 1-1z", "M8 11V7a4 4 0 0 1 8 0v4"],
    "trash": ["M3 6h18", "M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2", "M19 6v13a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6", "M10 11v6", "M14 11v6"],
    "eyeOff": ["M9.9 5.1A9.6 9.6 0 0 1 12 5c5 0 9 5 9 7a12 12 0 0 1-2.1 2.6", "M6.6 6.6C3.8 8 2 11 2 12c1 2 5 7 10 7a9 9 0 0 0 3.4-.7", "M3 3l18 18", "M9.9 9.9a3 3 0 0 0 4.2 4.2"],
    "fileText": ["M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z", "M14 2v6h6", "M9 13h6", "M9 17h6", "M9 9h1"],
    "history": ["M3 12a9 9 0 1 0 3-6.7L3 8", "M3 3v5h5", "M12 7v5l3.5 2"],
    "settings": ["M12.5 2h-1a2 2 0 0 0-2 2 1.7 1.7 0 0 1-.85 1.48l-.7.4a1.7 1.7 0 0 1-1.7 0l-.3-.16a2 2 0 0 0-2.73.73l-.5.87a2 2 0 0 0 .73 2.73l.3.18a1.7 1.7 0 0 1 .85 1.47v.8a1.7 1.7 0 0 1-.85 1.48l-.3.17a2 2 0 0 0-.73 2.73l.5.87a2 2 0 0 0 2.73.73l.3-.17a1.7 1.7 0 0 1 1.7 0l.7.4A1.7 1.7 0 0 1 9.5 20a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2 1.7 1.7 0 0 1 .85-1.48l.7-.4a1.7 1.7 0 0 1 1.7 0l.3.17a2 2 0 0 0 2.73-.73l.5-.87a2 2 0 0 0-.73-2.73l-.3-.17a1.7 1.7 0 0 1-.85-1.48v-.8a1.7 1.7 0 0 1 .85-1.47l.3-.18a2 2 0 0 0 .73-2.73l-.5-.87a2 2 0 0 0-2.73-.73l-.3.16a1.7 1.7 0 0 1-1.7 0l-.7-.4A1.7 1.7 0 0 1 14.5 4a2 2 0 0 0-2-2z", "M12 12m-3 0a3 3 0 1 0 6 0a3 3 0 1 0-6 0"],
    "folder": ["M4 5h4.5l2 2.2H20a1 1 0 0 1 1 1V19a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z"],
    "folderPlus": ["M4 5h4.5l2 2.2H20a1 1 0 0 1 1 1V19a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z", "M12 12v5", "M9.5 14.5h5"],
    "chevR": ["m9 6 6 6-6 6"], "chevL": ["m15 6-6 6 6 6"], "chevD": ["m6 9 6 6 6-6"],
    "check": ["M20 6 9 17l-5-5"],
    "clock": ["M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0-18 0", "M12 7v5l3 2"],
    "archive": ["M3 4h18v4H3z", "M5 8v11a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8", "M10 12h4"],
    "image": ["M3 5h18v14H3z", "M8.5 11a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z", "m21 16-5-5-7 7"],
    "code": ["m16 18 6-6-6-6", "m8 6-6 6 6 6"],
    "key": ["M14.5 9.5a4.5 4.5 0 1 0-3.6 4.4L13 16h2v2h2v2h3v-3l-3.5-3.5a4.5 4.5 0 0 0 .9-3.5z"],
    "database": ["M12 5m-8 0a8 3 0 1 0 16 0a8 3 0 1 0-16 0", "M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5", "M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"],
    "mail": ["M3 5h18v14H3z", "m3 6 9 6 9-6"],
    "phone": ["M21 16.4v2.5a2 2 0 0 1-2.2 2 19.6 19.6 0 0 1-8.5-3 19.3 19.3 0 0 1-6-6 19.6 19.6 0 0 1-3-8.6A2 2 0 0 1 3.3 3h2.5a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L7 10.6a16 16 0 0 0 6 6l1.1-1a2 2 0 0 1 2.1-.5c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"],
    "card": ["M3 6h18v12H3z", "M3 10h18"],
    "user": ["M12 7m-4 0a4 4 0 1 0 8 0a4 4 0 1 0-8 0", "M4 21a8 8 0 0 1 16 0"],
    "users": ["M9 8m-3.5 0a3.5 3.5 0 1 0 7 0a3.5 3.5 0 1 0-7 0", "M2 20a7 7 0 0 1 14 0", "M16 4.5a3.5 3.5 0 0 1 0 7", "M22 20a7 7 0 0 0-4-6.3"],
    "bolt": ["M13 2 4 14h6l-1 8 9-12h-6z"],
    "layers": ["m12 2 9 5-9 5-9-5z", "m3 12 9 5 9-5", "m3 17 9 5 9-5"],
    "drive": ["M4 5h16a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z", "M7 9h6", "M7 13h10", "M16 9h.01"],
    "refresh": ["M21 12a9 9 0 1 1-3-6.7", "M21 4v4h-4"],
    "cpu": ["M6 6h12v12H6z", "M10 10h4v4h-4z", "M9 2v2", "M15 2v2", "M9 20v2", "M15 20v2", "M2 9h2", "M2 15h2", "M20 9h2", "M20 15h2"],
    "list": ["M8 6h13", "M8 12h13", "M8 18h13", "M3 6h.01", "M3 12h.01", "M3 18h.01"],
    "grid": ["M3 3h7v7H3z", "M14 3h7v7h-7z", "M14 14h7v7h-7z", "M3 14h7v7H3z"],
    "checkCircle": ["M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0-18 0", "m8.4 12 2.4 2.4 4.8-4.8"],
    "download": ["M12 3v12", "m7 11 5 5 5-5", "M5 20h14"],
    "plus": ["M12 5v14", "M5 12h14"],
    "hardDrive": ["M4 5h16a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z", "M7 9h6", "M7 13h10", "M16 9h.01"],
    "pause": ["M7 5h3v14H7z", "M14 5h3v14h-3z"],
    "stop": ["M7 7h10v10H7z"],
}

ROLE_ICON = {"개발자": "code", "디자이너": "image", "기획자": "fileText",
             "PM": "layers", "전산사무": "drive"}


def line_icon(name: str, size: int = 18, color: str = "#565E6C", stroke: float = 2.0):
    """Lucide 라인 아이콘을 QPixmap 으로 렌더(QtSvg)."""
    from PySide6.QtCore import QByteArray, Qt
    from PySide6.QtGui import QPainter, QPixmap
    from PySide6.QtSvg import QSvgRenderer

    paths = ICON_PATHS.get(name)
    if not paths:
        pm = QPixmap(size, size); pm.fill(Qt.transparent); return pm
    body = "".join(f'<path d="{d}"/>' for d in paths)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
           f'stroke="{color}" stroke-width="{stroke}" stroke-linecap="round" '
           f'stroke-linejoin="round">{body}</svg>')
    r = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    r.render(p)
    p.end()
    return pm


def _shield_path(x: float, y: float, w: float, h: float):
    """라운드 방패 경로(QPainterPath)."""
    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QPainterPath

    p = QPainterPath()
    cx = x + w / 2
    p.moveTo(x + w * 0.16, y + h * 0.14)
    p.lineTo(x + w * 0.84, y + h * 0.14)         # 상단
    p.lineTo(x + w * 0.84, y + h * 0.52)         # 우측
    p.quadTo(QPointF(x + w * 0.84, y + h * 0.80),
             QPointF(cx, y + h * 0.94))          # 우하단 → 바닥 끝
    p.quadTo(QPointF(x + w * 0.16, y + h * 0.80),
             QPointF(x + w * 0.16, y + h * 0.52))  # 좌하단
    p.closeSubpath()
    return p


def shield_pixmap(size: int = 24, stroke: int = 2, color: str = "#FFFFFF",
                  bg: str | None = None, radius_ratio: float = 0.22):
    """흰색(기본) 외곽선 방패 픽스맵. bg 지정 시 라운드 사각 배경 위에 그린다."""
    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QPixmap

    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    pt = QPainter(pix)
    pt.setRenderHint(QPainter.Antialiasing, True)

    if bg:
        pt.setPen(Qt.NoPen)
        pt.setBrush(QBrush(QColor(bg)))
        r = size * radius_ratio
        pt.drawRoundedRect(QRectF(0, 0, size, size), r, r)

    m = size * 0.20
    pen = QPen(QColor(color))
    pen.setWidthF(max(1.5, stroke))
    pen.setJoinStyle(Qt.RoundJoin)
    pt.setPen(pen)
    pt.setBrush(Qt.NoBrush)
    pt.drawPath(_shield_path(m, m, size - 2 * m, size - 2 * m))
    pt.end()
    return pix


def app_icon():
    """앱/창 아이콘: 크림슨 라운드 배경 + 흰색 라인 방패(파랑 없음)."""
    from PySide6.QtGui import QIcon

    icon = QIcon()
    for s in (16, 24, 32, 48, 64, 128, 256):
        stroke = max(2, round(s * 0.05))
        icon.addPixmap(shield_pixmap(s, stroke=stroke, color="#FFFFFF", bg=CRIMSON))
    return icon


def logo_pixmap(height: int = 28, white: bool = False):
    """실제 브랜드 로고(assets/brand/) 로딩. 없으면 None.

    파일명: solideo_logo.png(기본), solideo_logo_white.png(어두운 배경용).
    """
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QPixmap

    name = "solideo_logo_white.png" if white else "solideo_logo.png"
    path = _BRAND / name
    if not path.exists() and white:
        path = _BRAND / "solideo_logo.png"   # 흰색본 없으면 기본본
    if not path.exists():
        return None
    pix = QPixmap(str(path))
    if pix.isNull():
        return None
    return pix.scaledToHeight(height, Qt.SmoothTransformation)
