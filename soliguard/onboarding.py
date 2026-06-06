"""최초 실행 온보딩 마법사 - 직무·자동점검·OCR 초기 설정.

설치 직후 첫 구동에서만 1회 표시되며, 사용자를 첫 점검까지 빠르게 안내한다.
PySide6 의존(데모/테스트 환경에 없으면 import 시점 실패 — app.py 가 분기).
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QLabel, QRadioButton,
    QVBoxLayout, QWizard, QWizardPage,
)

from .config import AppConfig, ScheduleConfig
from .profiles import PROFILE_OCR_DEFAULT

ROLES = ["개발자", "디자이너", "기획자", "PM", "전산사무"]
_FREQ_MAP = {
    "사용 안 함": (False, "weekly"),
    "매일": (True, "daily"),
    "매주(월요일)": (True, "weekly"),
    "매월(1일)": (True, "monthly"),
}


class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("SoliGuard에 오신 것을 환영합니다")
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("🛡  내 PC의 고객 데이터, 먼저 찾습니다"))
        for promise in (
            "✔ 모든 데이터는 이 PC 안에서만 처리됩니다",
            "✔ 체크섬 검증으로 정확하게 검출합니다",
            "✔ 법규·발주처 감사 대응 리포트를 발급합니다",
        ):
            lbl = QLabel(promise)
            lbl.setStyleSheet("color:#64748B; font-size:13px;")
            lay.addWidget(lbl)


class ProfilePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("어떤 업무를 하시나요?")
        lay = QVBoxLayout(self)
        self.group = QButtonGroup(self)
        for i, role in enumerate(ROLES):
            rb = QRadioButton(role)
            if i == 0:
                rb.setChecked(True)
            self.group.addButton(rb, i)
            lay.addWidget(rb)

    def selected_profile(self) -> str:
        return ROLES[self.group.checkedId()]


class SchedulePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("자동 점검 주기 & 이미지 검사")
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("정해진 주기에 자동으로 PC를 점검합니다."))
        self.freq = QComboBox()
        self.freq.addItems(list(_FREQ_MAP.keys()))
        self.freq.setCurrentText("매주(월요일)")
        lay.addWidget(self.freq)
        self.ocr = QCheckBox("이미지 속 신분증·계약서도 검사 (로컬 OCR)")
        self.ocr.setChecked(True)
        lay.addWidget(self.ocr)
        self.designer_hint = QLabel(
            "💡 디자이너 팁: PSD·XD는 자동 검사됩니다. Figma 검사는 "
            "설정 > 'Figma 클라우드 검사(고급)'에서 동의 후 사용하세요."
        )
        self.designer_hint.setStyleSheet("color:#64748B; font-size:12px;")
        self.designer_hint.setWordWrap(True)
        self.designer_hint.setVisible(False)
        lay.addWidget(self.designer_hint)

    def set_designer(self, is_designer: bool) -> None:
        self.designer_hint.setVisible(is_designer)


class OnboardingWizard(QWizard):
    completed = Signal(object)  # AppConfig

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SoliGuard 초기 설정")
        self.resize(560, 480)
        self.welcome = WelcomePage()
        self.profile = ProfilePage()
        self.schedule = SchedulePage()
        for p in (self.welcome, self.profile, self.schedule):
            self.addPage(p)
        self.currentIdChanged.connect(self._sync_designer_hint)
        self.button(QWizard.FinishButton).clicked.connect(self._finish)

    def _sync_designer_hint(self, _id: int) -> None:
        self.schedule.set_designer(self.profile.selected_profile() == "디자이너")

    def _finish(self) -> None:
        cfg = AppConfig.load()
        profile = self.profile.selected_profile()
        cfg.profile = profile
        enabled, freq = _FREQ_MAP[self.schedule.freq.currentText()]
        cfg.schedule = ScheduleConfig(
            enabled=enabled, frequency=freq, day_of_week="mon", hour=9, minute=0
        )
        if self.schedule.ocr.isChecked():
            cfg.ocr_mode = "local"
        else:
            cfg.ocr_mode = "off"
        cfg.save()
        self.completed.emit(cfg)
