"""디자인 토큰 → Qt 스타일시트(QSS) 변환 + 등급 표시 매핑.

이 모듈은 Qt에 의존하지 않는 순수 파이썬이라 단위 테스트가 가능하다.
값은 soliguard/docs/디자인토큰 매뉴얼의 design-tokens.json 과 일치한다.
"""

from __future__ import annotations

__all__ = [
    "TOKENS",
    "BRAND",
    "SEMANTIC",
    "build_qss",
    "GRADE_DISPLAY",
    "grade_color",
    "severity_color",
]

TOKENS = {
    "light": {
        "bg": "#F8FAFC", "surface": "#FFFFFF", "surfaceAlt": "#F1F5F9",
        "border": "#E2E8F0", "textPrimary": "#0F172A", "textSecondary": "#64748B",
        "rowHover": "#F1F5F9", "rowSelected": "#EFF6FF",
    },
    "dark": {
        "bg": "#0F172A", "surface": "#1E293B", "surfaceAlt": "#283548",
        "border": "#334155", "textPrimary": "#F1F5F9", "textSecondary": "#94A3B8",
        "rowHover": "#283548", "rowSelected": "#1E3A5F",
    },
}
BRAND = {"soliBlue": "#1E40AF", "deepNavy": "#172554", "skyBlue": "#3B82F6"}
SEMANTIC = {"safe": "#16A34A", "warn": "#D97706", "danger": "#DC2626"}

# 위험 등급(엔진 한국어 값) → (영문키, 색, 아이콘)
GRADE_DISPLAY = {
    "안전": {"key": "safe", "color": SEMANTIC["safe"], "icon": "🟢"},
    "주의": {"key": "warn", "color": SEMANTIC["warn"], "icon": "🟡"},
    "위험": {"key": "danger", "color": SEMANTIC["danger"], "icon": "🔴"},
}

# 위험도(Severity.value) → 색
_SEVERITY_COLOR = {
    "높음": SEMANTIC["danger"],
    "중간": SEMANTIC["warn"],
    "낮음": SEMANTIC["safe"],
}


def grade_color(grade: str) -> str:
    return GRADE_DISPLAY.get(grade, {}).get("color", "#64748B")


def severity_color(severity_value: str) -> str:
    return _SEVERITY_COLOR.get(severity_value, "#64748B")


def build_qss(theme: str = "light") -> str:
    """디자인 토큰을 Qt 전역 스타일시트로 변환."""
    t = TOKENS.get(theme, TOKENS["light"])
    sky = "#60A5FA" if theme == "dark" else BRAND["skyBlue"]
    return f"""
    QMainWindow, QWidget {{
        background: {t['bg']};
        color: {t['textPrimary']};
        font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
        font-size: 14px;
    }}
    #Sidebar {{ background: {BRAND['deepNavy']}; }}
    #Sidebar QLabel {{ color: white; }}
    #Sidebar QPushButton {{
        color: white; text-align: left; padding: 0 24px;
        min-height: 44px; border: none; border-radius: 0;
        background: transparent; font-size: 14px;
    }}
    #Sidebar QPushButton:hover {{ background: rgba(255,255,255,0.08); }}
    #Sidebar QPushButton:checked {{
        background: rgba(255,255,255,0.10);
        border-left: 4px solid {BRAND['soliBlue']};
    }}
    QFrame#Card {{
        background: {t['surface']};
        border: 1px solid {t['border']};
        border-radius: 12px;
    }}
    QPushButton#Primary {{
        background: {BRAND['soliBlue']}; color: white;
        border-radius: 8px; min-height: 40px; font-weight: 600;
    }}
    QPushButton#Primary:hover {{ background: #1B399E; }}
    QPushButton#Primary:pressed {{ background: #16317E; }}
    QPushButton#Primary:disabled {{ background: {t['border']}; color: {t['textSecondary']}; }}
    QPushButton#Danger {{
        background: {SEMANTIC['danger']}; color: white;
        border-radius: 8px; min-height: 40px;
    }}
    QProgressBar {{
        border: none; border-radius: 6px; background: {t['surfaceAlt']};
        height: 12px; text-align: center;
    }}
    QProgressBar::chunk {{ background: {sky}; border-radius: 6px; }}
    QTableWidget {{
        background: {t['surface']}; border: 1px solid {t['border']};
        border-radius: 12px; gridline-color: {t['border']};
    }}
    QHeaderView::section {{
        background: {t['surfaceAlt']}; color: {t['textSecondary']};
        padding: 8px; border: none; font-size: 12px;
    }}
    QTableWidget::item:hover {{ background: {t['rowHover']}; }}
    QTableWidget::item:selected {{ background: {t['rowSelected']}; color: {t['textPrimary']}; }}
    """
