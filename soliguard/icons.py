"""아이콘/로고 유틸 - 흰색 라인 방패, 앱 아이콘, 실제 브랜드 로고 로딩.

- 방패: 파랑 이모지 대신 흰색 2px 외곽선으로 그린다(QPainter).
- 로고: 실제 첨부 로고 파일(assets/brand/)을 우선 사용, 없으면 None.
"""

from __future__ import annotations

from pathlib import Path

_ASSETS = Path(__file__).resolve().parent.parent / "assets"
_BRAND = _ASSETS / "brand"

CRIMSON = "#B0123F"

__all__ = ["shield_pixmap", "app_icon", "logo_pixmap"]


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
