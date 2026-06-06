"""최초 실행 온보딩 - SolManager급 커스텀 디자인(스텝 인디케이터 + 카드).

기본 QWizard 대신, 브랜드 카드 + 단계 표시 + 크림슨 버튼으로 구성한 다이얼로그.
완료 시 completed(AppConfig) 시그널을 emit 한다(app.py 가 수신).
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QDialog, QFrame, QGraphicsDropShadowEffect,
    QGridLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget, QVBoxLayout,
    QWidget,
)

from . import fonts, icons
from .config import AppConfig, ScheduleConfig

ROLES = [("개발자", "💻"), ("디자이너", "🎨"), ("기획자", "📝"),
         ("PM", "📋"), ("전산사무", "🗂")]
_FREQ_MAP = {
    "사용 안 함": (False, "weekly"), "매일": (True, "daily"),
    "매주(월요일)": (True, "weekly"), "매월(1일)": (True, "monthly"),
}
_STEPS = ["직무", "점검 설정"]

_QSS = """
* { font-family: 'Pretendard'; }
#Backdrop { background: #EFE6EA; }
#Card { background: #FFFFFF; border-radius: 18px; }
#Brand { font-size: 17px; }
#Pill {
    background: #FCE4EC; color: #C8174E; border-radius: 11px;
    padding: 4px 12px; font-size: 12px; font-weight: 700;
}
#IconBadge { background: #C8174E; border-radius: 13px; color: white; font-size: 22px; }
#Title { font-size: 21px; font-weight: 800; color: #231815; }
#Sub { color: #7A6A70; font-size: 13px; }
#SectionLabel { font-size: 13px; font-weight: 700; color: #231815; }
#Trust {
    background: #FBEFF3; border: 1px solid #F3D9E1; border-radius: 10px;
    color: #8A4A5C; font-size: 12px;
}
#StepNumActive {
    background: #C8174E; color: white; border-radius: 14px; font-weight: 700;
}
#StepNumIdle { background: #E7DAE0; color: #9A8A90; border-radius: 14px; font-weight: 700; }
#StepTextActive { color: #231815; font-weight: 700; font-size: 13px; }
#StepTextIdle { color: #B0A0A6; font-size: 13px; }
#Connector { background: #E7DAE0; }
QPushButton#Primary {
    background: #C8174E; color: white; border: none; border-radius: 9px;
    min-height: 42px; padding: 0 24px; font-size: 14px; font-weight: 700;
}
QPushButton#Primary:hover { background: #B11343; }
QPushButton#Primary:pressed { background: #990F39; }
QPushButton#Ghost {
    background: transparent; color: #7A6A70; border: 1px solid #E7DCE0;
    border-radius: 9px; min-height: 42px; padding: 0 18px; font-size: 14px;
}
QPushButton#Ghost:hover { background: #F4EEF0; }
QPushButton#RoleCard {
    background: #FFFFFF; border: 1px solid #E7DCE0; border-radius: 12px;
    color: #231815; font-size: 14px; font-weight: 600; text-align: center;
}
QPushButton#RoleCard:hover { border-color: #E6A3BC; }
QPushButton#RoleCard:checked { border: 2px solid #C8174E; background: #FCE4EC; }
QComboBox {
    background: #FFFFFF; border: 1px solid #E7DCE0; border-radius: 8px;
    padding: 8px 12px; color: #231815; min-height: 20px;
}
QComboBox QAbstractItemView {
    background: white; color: #231815; selection-background-color: #C8174E;
    selection-color: white; outline: 0;
}
QCheckBox { color: #231815; font-size: 13px; }
"""


class OnboardingWizard(QDialog):
    completed = Signal(object)  # AppConfig

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SoliGuard 초기 설정")
        self.setObjectName("Backdrop")
        self.setMinimumSize(680, 600)
        self.setStyleSheet(_QSS)
        from PySide6.QtGui import QFont
        from PySide6.QtWidgets import QApplication

        fam = fonts.load_fonts(QApplication.instance())
        self.setFont(QFont(fam, 10))

        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 36, 40, 36)

        card = QFrame()
        card.setObjectName("Card")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(80, 10, 30, 60))
        card.setGraphicsEffect(shadow)
        outer.addWidget(card)

        c = QVBoxLayout(card)
        c.setContentsMargins(40, 32, 40, 28)
        c.setSpacing(18)

        # ── 상단: 브랜드 + 배지 ──
        top = QHBoxLayout()
        logo_pix = icons.logo_pixmap(26, white=False)
        if logo_pix is not None:
            brand = QLabel()
            brand.setPixmap(logo_pix)
        else:
            brand = QLabel(
                '<span style="color:#231815;font-weight:800;">solideo</span>'
                '<span style="color:#C8174E;font-weight:800;">S.</span>')
            brand.setObjectName("Brand")
        top.addWidget(brand)
        top.addStretch()
        pill = QLabel("SoliGuard · 초기 설정")
        pill.setObjectName("Pill")
        top.addWidget(pill)
        c.addLayout(top)

        # ── 아이콘 + 제목 ──
        title_row = QHBoxLayout()
        title_row.setSpacing(14)
        badge = QLabel()
        badge.setFixedSize(52, 52)
        badge.setPixmap(icons.shield_pixmap(52, stroke=3, color="#FFFFFF", bg="#C8174E"))
        badge.setAlignment(Qt.AlignCenter)
        title_row.addWidget(badge)
        tcol = QVBoxLayout()
        tcol.setSpacing(2)
        title = QLabel("SoliGuard에 오신 것을 환영합니다")
        title.setObjectName("Title")
        tcol.addWidget(title)
        sub = QLabel("처음 한 번만 설정하면 됩니다. 입력값은 이 PC에만 저장됩니다.")
        sub.setObjectName("Sub")
        tcol.addWidget(sub)
        title_row.addLayout(tcol)
        title_row.addStretch()
        c.addLayout(title_row)

        # ── 스텝 인디케이터 ──
        c.addLayout(self._build_steps())

        # ── 페이지 ──
        self.pages = QStackedWidget()
        self.pages.addWidget(self._page_role())
        self.pages.addWidget(self._page_schedule())
        c.addWidget(self.pages, 1)

        # ── 신뢰 박스 ──
        trust = QLabel("이 도구는 외부로 어떤 정보도 전송하지 않습니다. "
                       "모든 데이터는 이 PC의 로컬 저장소에만 보관됩니다.")
        trust.setObjectName("Trust")
        trust.setWordWrap(True)
        trust.setContentsMargins(14, 12, 14, 12)
        c.addWidget(trust)

        # ── 하단 버튼 ──
        nav = QHBoxLayout()
        self.back_btn = QPushButton("‹ 이전")
        self.back_btn.setObjectName("Ghost")
        self.back_btn.clicked.connect(self._prev)
        nav.addWidget(self.back_btn)
        nav.addStretch()
        self.next_btn = QPushButton("다음 ›")
        self.next_btn.setObjectName("Primary")
        self.next_btn.clicked.connect(self._next)
        nav.addWidget(self.next_btn)
        c.addLayout(nav)

        self._index = 0
        self._sync()

    # ---- 스텝 인디케이터 ----
    def _build_steps(self) -> QHBoxLayout:
        lay = QHBoxLayout()
        lay.setSpacing(8)
        self._step_nums, self._step_texts = [], []
        for i, name in enumerate(_STEPS):
            num = QLabel(str(i + 1))
            num.setFixedSize(28, 28)
            num.setAlignment(Qt.AlignCenter)
            self._step_nums.append(num)
            lay.addWidget(num)
            txt = QLabel(name)
            self._step_texts.append(txt)
            lay.addWidget(txt)
            if i < len(_STEPS) - 1:
                conn = QFrame()
                conn.setObjectName("Connector")
                conn.setFixedSize(40, 2)
                lay.addWidget(conn)
        lay.addStretch()
        return lay

    def _sync_steps(self):
        for i, (num, txt) in enumerate(zip(self._step_nums, self._step_texts)):
            active = i == self._index
            num.setObjectName("StepNumActive" if active else "StepNumIdle")
            txt.setObjectName("StepTextActive" if active else "StepTextIdle")
            for wgt in (num, txt):
                wgt.style().unpolish(wgt)
                wgt.style().polish(wgt)

    # ---- 페이지 1: 직무 ----
    def _page_role(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 6, 0, 0)
        lbl = QLabel("어떤 업무를 하시나요?")
        lbl.setObjectName("SectionLabel")
        lay.addWidget(lbl)
        hint = QLabel("선택한 직무에 맞춰 점검 항목과 추천 폴더가 자동 구성됩니다.")
        hint.setObjectName("Sub")
        lay.addWidget(hint)

        grid = QGridLayout()
        grid.setSpacing(10)
        self.role_group = QButtonGroup(self)
        for i, (role, icon) in enumerate(ROLES):
            b = QPushButton(f"{icon}\n{role}")
            b.setObjectName("RoleCard")
            b.setCheckable(True)
            b.setMinimumHeight(76)
            if i == 0:
                b.setChecked(True)
            self.role_group.addButton(b, i)
            grid.addWidget(b, i // 3, i % 3)
        lay.addLayout(grid)
        lay.addStretch()
        return w

    def selected_profile(self) -> str:
        return ROLES[max(0, self.role_group.checkedId())][0]

    # ---- 페이지 2: 점검 설정 ----
    def _page_schedule(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 6, 0, 0)
        lay.setSpacing(10)
        lbl = QLabel("자동 점검 주기")
        lbl.setObjectName("SectionLabel")
        lay.addWidget(lbl)
        self.freq = QComboBox()
        self.freq.addItems(list(_FREQ_MAP.keys()))
        self.freq.setCurrentText("매주(월요일)")
        lay.addWidget(self.freq)
        self.ocr = QCheckBox("이미지 속 신분증·계약서도 검사합니다 (로컬 OCR)")
        self.ocr.setChecked(True)
        lay.addWidget(self.ocr)
        self.designer_hint = QLabel(
            "💡 디자이너 팁: PSD·XD는 자동 검사됩니다. Figma 검사는 "
            "설정에서 동의 후 사용할 수 있습니다.")
        self.designer_hint.setObjectName("Sub")
        self.designer_hint.setWordWrap(True)
        self.designer_hint.setVisible(False)
        lay.addWidget(self.designer_hint)
        lay.addStretch()
        return w

    # ---- 네비게이션 ----
    def _sync(self):
        self.pages.setCurrentIndex(self._index)
        self.back_btn.setVisible(self._index > 0)
        last = self._index == len(_STEPS) - 1
        self.next_btn.setText("시작하기" if last else "다음 ›")
        if self._index == 1:
            self.designer_hint.setVisible(self.selected_profile() == "디자이너")
        self._sync_steps()

    def _next(self):
        if self._index < len(_STEPS) - 1:
            self._index += 1
            self._sync()
        else:
            self._finish()

    def _prev(self):
        if self._index > 0:
            self._index -= 1
            self._sync()

    def _finish(self):
        cfg = AppConfig.load()
        cfg.profile = self.selected_profile()
        enabled, freq = _FREQ_MAP[self.freq.currentText()]
        cfg.schedule = ScheduleConfig(
            enabled=enabled, frequency=freq, day_of_week="mon", hour=9, minute=0)
        cfg.ocr_mode = "local" if self.ocr.isChecked() else "off"
        cfg.save()
        self.completed.emit(cfg)
        self.accept()
