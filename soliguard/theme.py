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

# Solideo 브랜드 팔레트(크림슨). 로고 'solideoS.' 톤앤매너 기준.
BRAND = {
    "crimson": "#C8174E",      # 주요 액션·강조 (로고 'S.' 마크)
    "crimsonHover": "#B11343",
    "crimsonPressed": "#990F39",
    "maroonTop": "#4A1020",    # 사이드바 그라데이션 상단(딥 마룬)
    "maroonBottom": "#7A1838", # 사이드바 그라데이션 하단(크림슨 쪽)
    "rose": "#E11D62",         # 진행바·링크 강조
    "roseDark": "#F472A6",     # 다크 테마 강조
    "ink": "#231815",          # 워드마크 따뜻한 블랙
}
SEMANTIC = {"safe": "#16A34A", "warn": "#D97706", "danger": "#DC2626"}

TOKENS = {
    "light": {
        "bg": "#FAF7F8", "surface": "#FFFFFF", "surfaceAlt": "#F4EEF0",
        "border": "#E7DCE0", "textPrimary": "#231815", "textSecondary": "#7A6A70",
        "rowHover": "#FBEFF3", "rowSelected": "#FCE4EC",
    },
    "dark": {
        "bg": "#1A0E12", "surface": "#2A171D", "surfaceAlt": "#3A2028",
        "border": "#4A2A33", "textPrimary": "#F5ECEF", "textSecondary": "#C2A8B0",
        "rowHover": "#3A2028", "rowSelected": "#4A1628",
    },
}

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
    """디자인 토큰을 Qt 전역 스타일시트로 변환(Solideo 크림슨)."""
    t = TOKENS.get(theme, TOKENS["light"])
    accent = BRAND["roseDark"] if theme == "dark" else BRAND["rose"]
    return f"""
    QMainWindow, QWidget {{
        background: {t['bg']};
        color: {t['textPrimary']};
        font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
        font-size: 14px;
    }}
    #Sidebar {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {BRAND['maroonTop']}, stop:1 {BRAND['maroonBottom']});
    }}
    #Sidebar QLabel {{ color: white; }}
    #Sidebar QPushButton {{
        color: white; text-align: left; padding: 0 24px;
        min-height: 44px; border: none; border-radius: 0;
        background: transparent; font-size: 14px;
    }}
    #Sidebar QPushButton:hover {{ background: rgba(255,255,255,0.10); }}
    #Sidebar QPushButton:checked {{
        background: rgba(255,255,255,0.12);
        border-left: 4px solid {BRAND['rose']};
    }}
    QFrame#Card {{
        background: {t['surface']};
        border: 1px solid {t['border']};
        border-radius: 12px;
    }}
    QPushButton#Primary {{
        background: {BRAND['crimson']}; color: white;
        border-radius: 8px; min-height: 40px; font-weight: 600;
    }}
    QPushButton#Primary:hover {{ background: {BRAND['crimsonHover']}; }}
    QPushButton#Primary:pressed {{ background: {BRAND['crimsonPressed']}; }}
    QPushButton#Primary:disabled {{ background: {t['border']}; color: {t['textSecondary']}; }}
    QPushButton#Danger {{
        background: {SEMANTIC['danger']}; color: white;
        border-radius: 8px; min-height: 40px;
    }}
    QComboBox {{
        background: {t['surface']}; border: 1px solid {t['border']};
        border-radius: 6px; padding: 6px 10px; color: {t['textPrimary']};
        min-height: 20px;
    }}
    QComboBox::drop-down {{ border: none; width: 22px; }}
    QComboBox QAbstractItemView {{
        background: {t['surface']}; color: {t['textPrimary']};
        border: 1px solid {t['border']};
        selection-background-color: {BRAND['crimson']};
        selection-color: white; outline: 0;
    }}
    QLabel {{ background: transparent; }}
    QLineEdit, QCheckBox {{ color: {t['textPrimary']}; }}
    QLineEdit {{
        background: {t['surface']}; border: 1px solid {t['border']};
        border-radius: 6px; padding: 6px 8px;
    }}
    QGroupBox {{
        border: 1px solid {t['border']}; border-radius: 12px;
        margin-top: 12px; padding: 12px; font-weight: 600;
    }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 6px; }}
    QPushButton#Ghost {{
        background: transparent; color: {t['textSecondary']};
        border: 1px solid {t['border']}; border-radius: 8px;
        min-height: 36px; padding: 0 14px;
    }}
    QPushButton#Ghost:hover {{ background: {t['surfaceAlt']}; }}
    QProgressBar {{
        border: none; border-radius: 6px; background: {t['surfaceAlt']};
        height: 12px; text-align: center;
    }}
    QProgressBar::chunk {{ background: {accent}; border-radius: 6px; }}
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
