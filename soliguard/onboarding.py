"""최초 실행 온보딩 - 정본(docs/app install) 5단계 플로우.

환영 → 직무 선택(복수) → 스캔 폴더 → 자동 점검 → 이미지 검사.
상단 진행 점(progress dots) + 카드 디자인. 완료 시 completed(AppConfig) emit.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QDialog, QFrame,
    QGraphicsDropShadowEffect, QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QVBoxLayout, QWidget,
)

from . import fonts, icons
from .config import AppConfig, ScheduleConfig
from .profiles import ALL_PROFILES, PROFILE_DESC, PROFILE_FOLDERS
from .theme import BRAND

_CRIMSON = BRAND["brand"]


def _checkbox_pm(on: bool, size: int = 20):
    """둥근 사각 체크박스(정본 Box sq)."""
    from PySide6.QtCore import Qt as _Qt
    from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
    pm = QPixmap(size, size); pm.fill(_Qt.transparent)
    p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing, True)
    p.setPen(QPen(QColor(_CRIMSON if on else "#D6DAE2"), 1.7))
    p.setBrush(QColor(_CRIMSON) if on else QColor("#FFFFFF"))
    p.drawRoundedRect(1, 1, size - 2, size - 2, 6, 6)
    if on:
        p.drawPixmap(2, 2, icons.line_icon("check", size - 4, "#FFFFFF", 3))
    p.end()
    return pm


def _radio_pm(on: bool, size: int = 20):
    """원형 라디오(정본 Box 원형)."""
    from PySide6.QtCore import Qt as _Qt
    from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
    pm = QPixmap(size, size); pm.fill(_Qt.transparent)
    p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing, True)
    p.setPen(QPen(QColor(_CRIMSON if on else "#D6DAE2"), 1.7))
    p.setBrush(QColor(_CRIMSON) if on else QColor("#FFFFFF"))
    p.drawEllipse(1, 1, size - 2, size - 2)
    if on:
        p.setBrush(QColor("#FFFFFF")); p.setPen(_Qt.NoPen)
        d = size * 0.42
        p.drawEllipse(int((size - d) / 2), int((size - d) / 2), int(d), int(d))
    p.end()
    return pm


def _icon_box_pm(name: str, on: bool, size: int = 34):
    """라운드 사각 안 Lucide 아이콘(선택 시 크림슨 채움+흰 아이콘)."""
    from PySide6.QtCore import QRectF, Qt as _Qt
    from PySide6.QtGui import QColor, QPainter, QPixmap
    pm = QPixmap(size, size); pm.fill(_Qt.transparent)
    p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing, True)
    p.setPen(_Qt.NoPen)
    p.setBrush(QColor(_CRIMSON) if on else QColor("#F7F8FA"))
    p.drawRoundedRect(QRectF(0, 0, size, size), 9, 9)
    ic = icons.line_icon(name, round(size * 0.55), "#FFFFFF" if on else "#565E6C", 2)
    off = (size - ic.width()) // 2
    p.drawPixmap(off, off, ic)
    p.end()
    return pm

_STEPS = ["환영", "직무", "스캔 폴더", "자동 점검", "이미지 검사"]
_SCHED = [("off", "사용 안 함"), ("daily", "매일 09:00"),
          ("weekly", "매주 (월요일) 09:00"), ("monthly", "매월 1일 09:00")]

_QSS = """
#Backdrop { background: #F3F4F7; }
#Card { background: #FFFFFF; border: 1px solid #E7E9EE; border-radius: 16px; }
#Title { font-size: 22px; font-weight: 800; color: #14161C; }
#Sub { color: #565E6C; font-size: 13px; }
#Pill { background: #FCEFF3; color: #B0123F; border-radius: 11px; padding: 4px 12px; font-size: 12px; font-weight: 700; }
#DotActive { background: #B0123F; color: white; border-radius: 12px; font-weight: 700; font-size: 11px; }
#DotIdle { background: #EFF1F4; color: #8B92A0; border-radius: 12px; font-weight: 700; font-size: 11px; }
#StepLabel { color: #B0123F; font-weight: 700; font-size: 12.5px; }
#Conn { background: #E7E9EE; }
#Trust { background: #FCEFF3; border: 1px solid #F6D2DE; border-radius: 10px; color: #5E0A24; font-size: 12px; }
QPushButton#Primary { background: #B0123F; color: white; border: none; border-radius: 10px;
    min-height: 42px; padding: 0 22px; font-size: 14px; font-weight: 700; }
QPushButton#Primary:hover { background: #C7164A; }
QPushButton#Primary:pressed { background: #930E33; }
QPushButton#Ghost { background: #FFFFFF; color: #14161C; border: 1px solid #D6DAE2;
    border-radius: 10px; min-height: 42px; padding: 0 18px; font-size: 13.5px; font-weight: 700; }
QPushButton#Ghost:hover { background: #F7F8FA; }
QPushButton#ChkCard { background: #FFFFFF; border: 1px solid #E7E9EE; border-radius: 12px;
    color: #14161C; font-size: 13.5px; font-weight: 600; text-align: left; padding: 12px 14px; }
QPushButton#ChkCard:hover { border-color: #EEB6C8; }
QPushButton#ChkCard:checked { border: 2px solid #B0123F; background: #FCEFF3; color: #B0123F; }
QLabel { background: transparent; }
"""


def _promise_card(icon_name, title, desc) -> QFrame:
    f = QFrame()
    f.setObjectName("Card")
    v = QVBoxLayout(f)
    v.setContentsMargins(16, 14, 16, 14)
    badge = QLabel()
    badge.setFixedSize(36, 36)
    badge.setAlignment(Qt.AlignCenter)
    badge.setStyleSheet("background:#FCEFF3; border-radius:10px;")
    badge.setPixmap(icons.line_icon(icon_name, 19, _CRIMSON, 2))
    v.addWidget(badge)
    t = QLabel(title)
    t.setStyleSheet("font-weight:700; font-size:13.5px;")
    v.addWidget(t)
    d = QLabel(desc)
    d.setWordWrap(True)
    d.setStyleSheet("color:#565E6C; font-size:11.5px;")
    v.addWidget(d)
    return f


class OnboardingWizard(QDialog):
    completed = Signal(object)  # AppConfig

    def __init__(self):
        super().__init__()
        self.setWindowTitle("솔리가드 — 초기 설정")
        self.setObjectName("Backdrop")
        self.setMinimumSize(680, 600)
        self.setStyleSheet(_QSS)
        fonts.load_fonts(QApplication.instance())  # 앱 폰트(Pretendard·AA) 상속

        self.roles = ["개발자"]
        self.sched = "weekly"
        self.ocr = True
        self._folder_checks = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 34, 40, 34)
        card = QFrame()
        card.setObjectName("Card")
        sh = QGraphicsDropShadowEffect(self)
        sh.setBlurRadius(40)
        sh.setOffset(0, 8)
        sh.setColor(QColor(80, 10, 30, 55))
        card.setGraphicsEffect(sh)
        outer.addWidget(card)

        c = QVBoxLayout(card)
        c.setContentsMargins(34, 26, 34, 22)
        c.setSpacing(14)

        # 상단: solideo 로고 + 배지
        top = QHBoxLayout(); top.setSpacing(10)
        _logo = icons.logo_pixmap(24, white=False)
        if _logo is not None:
            brand = QLabel(); brand.setPixmap(_logo)
        else:
            brand = QLabel(f'솔리<span style="color:{_CRIMSON};font-weight:800;">가드</span>')
            brand.setStyleSheet("font-size:16px; font-weight:800;")
        top.addWidget(brand)
        top.addStretch()
        pill = QLabel("SoliGuard · 초기 설정")
        pill.setObjectName("Pill")
        top.addWidget(pill)
        c.addLayout(top)

        # 진행 점
        c.addLayout(self._build_dots())

        # 페이지
        self.pages = QStackedWidget()
        self.pages.addWidget(self._page_welcome())
        self.pages.addWidget(self._page_roles())
        self.folder_page = self._page_folders()
        self.pages.addWidget(self.folder_page)
        self.pages.addWidget(self._page_schedule())
        self.pages.addWidget(self._page_ocr())
        c.addWidget(self.pages, 1)

        # 하단 버튼
        nav = QHBoxLayout()
        self.back_btn = QPushButton("  이전")
        self.back_btn.setObjectName("Ghost")
        self.back_btn.setIcon(QIcon(icons.line_icon("chevL", 16, "#565E6C", 2.4)))
        self.back_btn.clicked.connect(self._prev)
        nav.addWidget(self.back_btn)
        nav.addStretch()
        self.next_btn = QPushButton("다음  ")
        self.next_btn.setObjectName("Primary")
        self.next_btn.clicked.connect(self._next)
        nav.addWidget(self.next_btn)
        c.addLayout(nav)

        self._index = 0
        self._sync()

    # ---- 진행 점 ----
    def _build_dots(self) -> QHBoxLayout:
        lay = QHBoxLayout()
        lay.setSpacing(7)
        self._dots, self._labels, self._conns = [], [], []
        for i, name in enumerate(_STEPS):
            num = QLabel(str(i + 1))
            num.setFixedSize(24, 24)
            num.setAlignment(Qt.AlignCenter)
            self._dots.append(num)
            lay.addWidget(num)
            lbl = QLabel(name)
            lbl.setObjectName("StepLabel")
            self._labels.append(lbl)
            lay.addWidget(lbl)
            if i < len(_STEPS) - 1:
                conn = QFrame()
                conn.setObjectName("Conn")
                conn.setFixedHeight(2)
                conn.setMinimumWidth(16)
                self._conns.append(conn)
                lay.addWidget(conn, 1)
        return lay

    def _sync_dots(self):
        for i, (num, lbl) in enumerate(zip(self._dots, self._labels)):
            num.setObjectName("DotActive" if i <= self._index else "DotIdle")
            num.setText("✓" if i < self._index else str(i + 1))
            lbl.setVisible(i == self._index)
            num.style().unpolish(num); num.style().polish(num)

    # ---- 페이지 1: 환영 ----
    def _page_welcome(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(6)
        v.setAlignment(Qt.AlignTop)
        badge = QLabel()
        badge.setFixedSize(60, 60)
        badge.setPixmap(icons.shield_pixmap(60, stroke=3, color="#FFFFFF", bg="#B0123F"))
        badge.setAlignment(Qt.AlignCenter)
        h = QHBoxLayout(); h.addStretch(); h.addWidget(badge); h.addStretch()
        v.addLayout(h)
        t = QLabel("내 PC의 고객 데이터, 먼저 찾습니다")
        t.setObjectName("Title"); t.setAlignment(Qt.AlignCenter)
        v.addWidget(t)
        s = QLabel("프로젝트가 끝나면, 데이터도 깨끗하게 — 솔리가드")
        s.setObjectName("Sub"); s.setAlignment(Qt.AlignCenter)
        v.addWidget(s)
        grid = QHBoxLayout()
        grid.setSpacing(12)
        grid.addWidget(_promise_card("shield", "로컬 처리", "모든 데이터는 이 PC 안에서만 처리되고 외부로 전송되지 않습니다"))
        grid.addWidget(_promise_card("checkCircle", "정확한 검출", "체크섬·Luhn·엔트로피 2단계 검증으로 오탐을 줄입니다"))
        grid.addWidget(_promise_card("fileText", "법규 증빙", "발주처 보안 감사·개인정보보호법 대응 리포트를 발급합니다"))
        v.addSpacing(8)
        v.addLayout(grid)
        v.addStretch()
        return w

    # ---- 페이지 2: 직무(복수) ----
    def _page_roles(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(6)
        h2 = QLabel("어떤 업무를 하시나요?")
        h2.setStyleSheet("font-size:18px; font-weight:800;")
        v.addWidget(h2)
        sub = QLabel("선택한 직무에 맞춰 점검 항목을 구성합니다. 복수 선택할 수 있어요.")
        sub.setObjectName("Sub")
        v.addWidget(sub)
        col = QVBoxLayout()
        col.setSpacing(9)
        self._role_checks = {}
        for role in ALL_PROFILES:
            col.addWidget(self._onb_role_card(role))
        v.addLayout(col)
        v.addStretch()
        return w

    def _onb_role_card(self, role: str) -> QPushButton:
        on = role in self.roles
        b = QPushButton(); b.setObjectName("ChkCard")
        b.setCheckable(True); b.setChecked(on)
        b.setMinimumHeight(60)
        h = QHBoxLayout(b); h.setContentsMargins(13, 10, 13, 10); h.setSpacing(12)
        chk = QLabel(); chk.setFixedSize(20, 20); chk.setPixmap(_checkbox_pm(on))
        h.addWidget(chk)
        icn = icons.ROLE_ICON.get(role, "user")
        ib = QLabel(); ib.setFixedSize(34, 34); ib.setPixmap(_icon_box_pm(icn, on))
        h.addWidget(ib)
        c = QVBoxLayout(); c.setSpacing(2)
        nm = QLabel(role)
        nm.setStyleSheet(f"font-weight:700; font-size:13px;"
                         f"color:{_CRIMSON if on else '#14161C'};")
        c.addWidget(nm)
        ds = QLabel(PROFILE_DESC.get(role, ""))
        ds.setStyleSheet("color:#565E6C; font-size:11.5px;")
        c.addWidget(ds)
        h.addLayout(c, 1)
        self._role_checks[role] = b

        def toggled(checked, r=role, cb=chk, ibx=ib, name=nm, ic=icn):
            cb.setPixmap(_checkbox_pm(checked))
            ibx.setPixmap(_icon_box_pm(ic, checked))
            name.setStyleSheet(f"font-weight:700; font-size:13px;"
                               f"color:{_CRIMSON if checked else '#14161C'};")
            sel = [x for x in ALL_PROFILES if self._role_checks[x].isChecked()]
            if not sel:  # 최소 1개 유지
                cb2 = self._role_checks[r]
                cb2.blockSignals(True); cb2.setChecked(True); cb2.blockSignals(False)
                cb.setPixmap(_checkbox_pm(True)); ibx.setPixmap(_icon_box_pm(ic, True))
                name.setStyleSheet(f"font-weight:700; font-size:13px; color:{_CRIMSON};")
                sel = [r]
            self.roles = sel
        b.toggled.connect(toggled)
        return b

    # ---- 페이지 3: 스캔 폴더 ----
    def _page_folders(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(6)
        h2 = QLabel("스캔할 폴더를 확인하세요")
        h2.setStyleSheet("font-size:18px; font-weight:800;")
        v.addWidget(h2)
        self.folder_sub = QLabel("직무에 맞춰 추천 폴더가 미리 선택돼 있어요.")
        self.folder_sub.setObjectName("Sub")
        v.addWidget(self.folder_sub)
        self.folder_box = QVBoxLayout()
        self.folder_box.setSpacing(8)
        v.addLayout(self.folder_box)
        v.addStretch()
        return w

    def _refresh_folders(self):
        # 기존 제거
        while self.folder_box.count():
            it = self.folder_box.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        self._folder_checks = []
        home = Path.home()
        names = ["Downloads", "Desktop", "Documents", "Pictures"]
        names += [n for role in self.roles for n in PROFILE_FOLDERS.get(role, [])]
        # 실제 존재하는 폴더만 노출(없는 추천 폴더는 숨김). (경로, 기본선택여부)
        rows, seen = [], set()
        for n in names:
            p = home / n
            key = str(p).lower()
            if key in seen:
                continue
            try:
                if p.exists() and p.is_dir():
                    seen.add(key); rows.append((p, True))   # 추천 폴더 기본 선택
            except OSError:
                continue
        for od in (home / "OneDrive", home / "OneDrive - Personal"):
            if od.exists() and str(od).lower() not in seen:
                seen.add(str(od).lower()); rows.append((od, False))  # OneDrive 기본 해제
        for p, on in rows:
            b = QPushButton(); b.setObjectName("ChkCard")
            b.setCheckable(True); b.setChecked(on); b.setMinimumHeight(44)
            h = QHBoxLayout(b); h.setContentsMargins(13, 9, 13, 9); h.setSpacing(11)
            chk = QLabel(); chk.setFixedSize(20, 20); chk.setPixmap(_checkbox_pm(on))
            h.addWidget(chk)
            fic = QLabel(); fic.setFixedSize(16, 16)
            fic.setPixmap(icons.line_icon("folder", 16, "#565E6C", 2))
            h.addWidget(fic)
            pl = QLabel(str(p))
            pl.setStyleSheet("font-family:'JetBrains Mono','D2Coding',monospace;"
                             "font-size:12px; color:#14161C;")
            h.addWidget(pl); h.addStretch()
            b.toggled.connect(lambda c, cb=chk: cb.setPixmap(_checkbox_pm(c)))
            self.folder_box.addWidget(b)
            self._folder_checks.append((b, str(p)))
        self.folder_sub.setText(f"직무 “{', '.join(self.roles)}”에 맞춰 추천 폴더가 미리 선택돼 있어요.")

    # ---- 페이지 4: 자동 점검 ----
    def _page_schedule(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(6)
        h2 = QLabel("자동 점검 주기를 설정하세요")
        h2.setStyleSheet("font-size:18px; font-weight:800;")
        v.addWidget(h2)
        sub = QLabel("정해진 주기에 백그라운드에서 자동으로 PC를 점검합니다.")
        sub.setObjectName("Sub")
        v.addWidget(sub)
        self._sched_group = QButtonGroup(self)
        self._sched_btns = {}
        for key, label in _SCHED:
            on = key == self.sched
            b = QPushButton(); b.setObjectName("ChkCard")
            b.setCheckable(True); b.setChecked(on); b.setMinimumHeight(48)
            h = QHBoxLayout(b); h.setContentsMargins(14, 10, 14, 10); h.setSpacing(11)
            rd = QLabel(); rd.setFixedSize(20, 20); rd.setPixmap(_radio_pm(on))
            h.addWidget(rd)
            ic = QLabel(); ic.setFixedSize(17, 17)
            ic.setPixmap(icons.line_icon("clock", 17, _CRIMSON if on else "#565E6C", 2))
            h.addWidget(ic)
            t = QLabel(label); t.setStyleSheet("font-size:13.5px; font-weight:600;")
            h.addWidget(t)
            h.addStretch()
            if key == "weekly":
                rec = QLabel("권장")
                rec.setStyleSheet("background:#E7F6EC; color:#15A34A; border-radius:8px;"
                                  "padding:2px 8px; font-size:11px; font-weight:700;")
                h.addWidget(rec)
            b.clicked.connect(lambda _=False, k=key: (setattr(self, "sched", k),
                                                      self._sync_sched()))
            self._sched_group.addButton(b)
            self._sched_btns[key] = (b, rd, ic)
            v.addWidget(b)
        v.addStretch()
        return w

    def _sync_sched(self):
        for key, (b, rd, ic) in self._sched_btns.items():
            on = b.isChecked()
            rd.setPixmap(_radio_pm(on))
            ic.setPixmap(icons.line_icon("clock", 17, _CRIMSON if on else "#565E6C", 2))

    # ---- 페이지 5: 이미지 검사 ----
    def _page_ocr(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(10)
        h2 = QLabel("이미지 속 정보도 검사할까요?")
        h2.setStyleSheet("font-size:18px; font-weight:800;")
        v.addWidget(h2)
        sub = QLabel("시안·스캔본 이미지 속 신분증·계약서를 OCR로 검출합니다.")
        sub.setObjectName("Sub")
        v.addWidget(sub)
        self.ocr_btn = QPushButton(); self.ocr_btn.setObjectName("ChkCard")
        self.ocr_btn.setCheckable(True); self.ocr_btn.setChecked(self.ocr)
        self.ocr_btn.setMinimumHeight(64)
        oh = QHBoxLayout(self.ocr_btn); oh.setContentsMargins(16, 12, 16, 12); oh.setSpacing(13)
        self._ocr_iconbox = QLabel(); self._ocr_iconbox.setFixedSize(44, 44)
        self._ocr_iconbox.setPixmap(_icon_box_pm("image", self.ocr, 44))
        oh.addWidget(self._ocr_iconbox)
        oc = QVBoxLayout(); oc.setSpacing(2)
        ot = QLabel("이미지 속 신분증·계약서 검사 (로컬 OCR)")
        ot.setStyleSheet("font-size:14px; font-weight:700;")
        oc.addWidget(ot)
        od = QLabel("이미지는 PC를 벗어나지 않고 로컬에서 분석됩니다")
        od.setStyleSheet("color:#565E6C; font-size:12px;")
        oc.addWidget(od)
        oh.addLayout(oc, 1)
        self._ocr_check = QLabel(); self._ocr_check.setFixedSize(20, 20)
        self._ocr_check.setPixmap(_checkbox_pm(self.ocr))
        oh.addWidget(self._ocr_check)

        def _ocr_toggle(on):
            self.ocr = on
            self._ocr_iconbox.setPixmap(_icon_box_pm("image", on, 44))
            self._ocr_check.setPixmap(_checkbox_pm(on))
        self.ocr_btn.toggled.connect(_ocr_toggle)
        v.addWidget(self.ocr_btn)
        trust = QLabel("외부 OCR API는 이미지가 PC를 벗어나므로 기본 비활성입니다. "
                       "필요 시 설정에서 명시적 동의 후에만 켤 수 있습니다.")
        trust.setObjectName("Trust")
        trust.setWordWrap(True)
        trust.setContentsMargins(14, 12, 14, 12)
        v.addWidget(trust)
        v.addStretch()
        return w

    # ---- 네비게이션 ----
    def _sync(self):
        self.pages.setCurrentIndex(self._index)
        self.back_btn.setVisible(self._index > 0)
        last = self._index == len(_STEPS) - 1
        from PySide6.QtGui import QIcon
        if last:
            self.next_btn.setText("  지금 첫 점검 시작")
            self.next_btn.setIcon(QIcon(icons.line_icon("search", 16, "#FFFFFF", 2.4)))
        else:
            self.next_btn.setText("다음  ")
            self.next_btn.setIcon(QIcon(icons.line_icon("chevR", 16, "#FFFFFF", 2.4)))
        if self._index == 2:
            self._refresh_folders()
        self._sync_dots()

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
        cfg.profiles = list(self.roles)
        cfg.profile = self.roles[0]
        folders = [p for b, p in self._folder_checks if b.isChecked()]
        if folders:
            cfg.target_folders = folders
        enabled = self.sched != "off"
        cfg.schedule = ScheduleConfig(
            enabled=enabled, frequency=(self.sched if enabled else "weekly"),
            day_of_week="mon", hour=9, minute=0)
        cfg.ocr_mode = "local" if self.ocr else "off"
        cfg.save()
        self.completed.emit(cfg)
        self.accept()
