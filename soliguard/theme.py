"""디자인 토큰 → Qt 스타일시트(QSS). 정본(docs/app/tokens.css) 기준.

solideo 크림슨 · 라이트 테마. 흰 사이드바 + 쿨그레이 배경.
Qt 비의존 순수 모듈이라 단위 테스트 가능.
"""

from __future__ import annotations

from pathlib import Path

__all__ = [
    "TOKENS", "BRAND", "SEMANTIC", "build_qss",
    "GRADE_DISPLAY", "grade_color", "severity_color", "SEV_CHIP",
]

# QSS image url 용 자산 경로(forward-slash). 없으면 빈 문자열로 graceful.
_ASSET_DIR = Path(__file__).resolve().parent.parent / "assets"


def _asset_url(name: str) -> str:
    p = _ASSET_DIR / name
    return p.as_posix() if p.exists() else ""

# Brand — solideo crimson (tokens.css)
BRAND = {
    "brand": "#B0123F",
    "strong": "#C7164A",
    "press": "#930E33",
    "deep": "#7E0C30",
    "ink": "#5E0A24",
    "pink50": "#FCEFF3",
    "pink100": "#FBE7EE",
    "pink200": "#F6D2DE",
}

SEMANTIC = {"safe": "#15A34A", "warn": "#E08600", "danger": "#E11D2A"}

TOKENS = {
    "light": {
        "bg": "#F3F4F7", "surface": "#FFFFFF", "surfaceAlt": "#F7F8FA",
        "border": "#E7E9EE", "borderStrong": "#D6DAE2",
        "text": "#14161C", "text2": "#565E6C", "text3": "#8B92A0",
        "rowHover": "#F7F8FA", "rowSelected": "#FCEFF3",
    },
    "dark": {
        "bg": "#14161C", "surface": "#1E2128", "surfaceAlt": "#262A33",
        "border": "#2E333D", "borderStrong": "#3A4049",
        "text": "#F1F2F4", "text2": "#AEB6C2", "text3": "#7E8694",
        "rowHover": "#262A33", "rowSelected": "#2A1620",
    },
}

# 위험 등급(엔진 한국어) → 표시
GRADE_DISPLAY = {
    "안전": {"key": "safe", "color": SEMANTIC["safe"], "icon": "🟢"},
    "주의": {"key": "warn", "color": SEMANTIC["warn"], "icon": "🟡"},
    "위험": {"key": "danger", "color": SEMANTIC["danger"], "icon": "🔴"},
}

# 위험도(Severity.value) → (글자색, 배경, 테두리) 칩 색
SEV_CHIP = {
    "높음": ("#E11D2A", "#FDEAEA", "#F6C4C4"),
    "중간": ("#E08600", "#FEF3E0", "#F6DDAE"),
    "낮음": ("#15A34A", "#E7F6EC", "#BBE6C8"),
}


def grade_color(grade: str) -> str:
    return GRADE_DISPLAY.get(grade, {}).get("color", "#8B92A0")


def severity_color(severity_value: str) -> str:
    return SEV_CHIP.get(severity_value, ("#8B92A0",))[0]


def build_qss(theme: str = "light") -> str:
    t = TOKENS.get(theme, TOKENS["light"])
    b = BRAND
    try:
        from .fonts import active_family
        fam = active_family()
    except Exception:
        fam = "Pretendard SG"
    return f"""
    /* 배경은 QWidget 전역에 칠하지 않는다(커스텀 위젯이 카드 위에서 회색 박스로
       보이는 현상 방지). 캔버스 배경은 창/다이얼로그에만 준다. */
    QWidget {{
        color: {t['text']};
        font-family: '{fam}';
        font-size: 13px;
    }}
    QMainWindow, QDialog {{ background: {t['bg']}; }}
    QLabel {{ background: transparent; }}

    /* ---- 사이드바 (흰색) ---- */
    #Sidebar {{ background: {t['surface']}; border-right: 1px solid {t['border']}; }}
    #Sidebar QLabel {{ background: transparent; color: {t['text']}; }}
    QPushButton#Nav {{
        text-align: left; padding: 0 12px; min-height: 42px; border: none;
        border-radius: 8px; background: transparent; color: {t['text2']};
        font-size: 13.5px; font-weight: 600;
    }}
    QPushButton#Nav:hover {{ background: {t['surfaceAlt']}; color: {t['text']}; }}
    QPushButton#Nav:checked {{
        background: {b['pink50']}; color: {b['brand']};
        border-left: 3px solid {b['brand']};
    }}
    QFrame#RoleChip {{
        background: {t['surface']}; border: 1px solid {t['border']};
        border-radius: 10px;
    }}
    QFrame#RoleChip:hover {{ border-color: {t['borderStrong']}; }}

    /* ---- 카드 ---- */
    QFrame#Card {{
        background: {t['surface']}; border: 1px solid {t['border']};
        border-radius: 16px;
    }}

    /* ---- 버튼 ---- */
    QPushButton#Primary {{
        background: {b['brand']}; color: #fff; border: none; border-radius: 10px;
        min-height: 40px; padding: 0 18px; font-size: 13.5px; font-weight: 700;
    }}
    QPushButton#Primary:hover {{ background: {b['strong']}; }}
    QPushButton#Primary:pressed {{ background: {b['press']}; }}
    QPushButton#Primary:disabled {{ background: {b['pink200']}; color: #fff; }}
    QPushButton#Ghost {{
        background: {t['surface']}; color: {t['text']};
        border: 1px solid {t['borderStrong']}; border-radius: 10px;
        min-height: 38px; padding: 0 16px; font-weight: 700; font-size: 13px;
    }}
    QPushButton#Ghost:hover {{ background: {t['surfaceAlt']}; }}
    QPushButton#Danger {{
        background: {SEMANTIC['danger']}; color: #fff; border: none;
        border-radius: 10px; min-height: 38px; padding: 0 16px; font-weight: 700;
    }}
    QPushButton#Danger:hover {{ background: #C8121E; }}

    /* ---- 입력 ---- */
    QComboBox, QLineEdit {{
        background: {t['surface']}; border: 1px solid {t['borderStrong']};
        border-radius: 8px; padding: 7px 10px; color: {t['text']};
        selection-background-color: {b['brand']}; selection-color: #fff;
    }}
    QComboBox::drop-down {{ border: none; width: 26px; }}
    QComboBox::down-arrow {{ image: url("{_asset_url('chevron-down.svg')}"); width: 13px; height: 13px; }}
    QComboBox QAbstractItemView {{
        background: {t['surface']}; color: {t['text']};
        border: 1px solid {t['border']}; border-radius: 8px; padding: 4px;
        selection-background-color: {b['pink50']}; selection-color: {b['brand']};
        outline: 0;
    }}
    QCheckBox {{ color: {t['text']}; spacing: 8px; }}
    QCheckBox::indicator {{
        width: 18px; height: 18px; border-radius: 5px;
        border: 1.6px solid {t['borderStrong']}; background: {t['surface']};
    }}
    QCheckBox::indicator:hover {{ border-color: {b['brand']}; }}
    QCheckBox::indicator:checked {{
        background: {b['brand']}; border-color: {b['brand']};
        image: url("{_asset_url('check-white.svg')}");
    }}

    /* ---- 그룹박스(예: Figma 고급 섹션) ---- */
    QGroupBox {{
        background: {t['surface']}; border: 1px solid {t['border']}; border-radius: 12px;
        margin-top: 12px; padding: 18px 18px 16px;
        font-size: 13px; font-weight: 800; color: {t['text']};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin; subcontrol-position: top left;
        left: 16px; top: 1px; padding: 0 6px; background: {t['surface']};
    }}
    QGroupBox::indicator {{
        width: 18px; height: 18px; border-radius: 5px;
        border: 1.6px solid {t['borderStrong']}; background: {t['surface']};
    }}
    QGroupBox::indicator:checked {{
        background: {b['brand']}; border-color: {b['brand']};
        image: url("{_asset_url('check-white.svg')}");
    }}

    /* ---- 표 ---- */
    QTableWidget {{
        background: {t['surface']}; border: 1px solid {t['border']};
        border-radius: 12px; gridline-color: {t['border']};
        selection-background-color: {t['rowSelected']};
    }}
    QHeaderView::section {{
        background: {t['surfaceAlt']}; color: {t['text3']};
        padding: 8px 10px; border: none; border-bottom: 1px solid {t['border']};
        font-size: 11.5px; font-weight: 700;
    }}
    QTableWidget::item {{ padding: 6px 8px; color: {t['text']}; }}
    QTableWidget::item:hover {{ background: {t['rowHover']}; }}
    QTableWidget::item:selected {{ background: {t['rowSelected']}; color: {t['text']}; }}

    /* ---- 진행바 ---- */
    QProgressBar {{
        border: none; border-radius: 7px; background: {t['surfaceAlt']};
        height: 14px; text-align: center; color: {t['text2']};
    }}
    QProgressBar::chunk {{ background: {b['brand']}; border-radius: 7px; }}

    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: #CDD2DB; border-radius: 5px; min-height: 30px; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
    """
