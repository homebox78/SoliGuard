"""설치 마법사 — 정본(docs/app/install.jsx Installer) 6단계 플로우 1:1 구현.

환영 → 사용권 계약 → 설치 위치 → 구성요소 → 설치(진행) → 완료.
프레임리스 창 + 크림슨 좌측 레일(단계 표시) + 우측 콘텐츠/푸터.
Lucide 라인 아이콘 + Pretendard. 완료 시 finished_install(run_now) emit.

실행:  py -m soliguard.installer
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QFileDialog, QFrame, QGraphicsDropShadowEffect,
    QHBoxLayout, QLabel, QLineEdit, QProgressBar, QPushButton, QScrollArea,
    QStackedWidget, QVBoxLayout, QWidget,
)

from . import fonts, icons
from .theme import BRAND, SEMANTIC, TOKENS

T = TOKENS["light"]
SAFE = SEMANTIC["safe"]
SAFE_BG = "#E7F6EC"

STEPS = ["환영", "사용권 계약", "설치 위치", "구성요소", "설치", "완료"]


def _qss(fam: str) -> str:
    b = BRAND
    return f"""
    * {{ font-family: '{fam}'; color: {T['text']}; }}
    #Win {{ background: {T['surface']}; border-radius: 12px; }}
    #Titlebar {{ border-bottom: 1px solid {T['border']}; }}
    #TbTitle {{ color: {T['text2']}; font-size: 12.5px; font-weight: 600; }}
    QPushButton#TbBtn {{ background: transparent; border: none; border-radius: 0; }}
    QPushButton#TbBtn:hover {{ background: #EEF0F3; }}
    QPushButton#TbClose:hover {{ background: #E81123; }}

    #Rail {{ border-top-left-radius: 12px; border-bottom-left-radius: 12px; }}
    #RailBrand {{ color: #fff; font-size: 17px; font-weight: 800; }}
    #RailSub {{ color: rgba(255,255,255,0.72); font-size: 11px; }}
    #RailFoot {{ color: rgba(255,255,255,0.7); font-size: 11px; }}

    #Title {{ font-size: 21px; font-weight: 800; letter-spacing: -0.02em; }}
    #H2 {{ font-size: 19px; font-weight: 800; }}
    #Sub {{ color: {T['text2']}; font-size: 13px; }}
    #Body {{ color: {T['text2']}; font-size: 13.5px; }}
    #Foot {{ border-top: 1px solid {T['border']}; }}
    #StepTag {{ color: {T['text3']}; font-size: 12px; font-weight: 600; }}

    QFrame#InfoBox {{ background: {T['surfaceAlt']}; border: 1px solid {T['border']}; border-radius: 12px; }}
    QFrame#Chip {{ background: #fff; border: 1px solid {T['border']}; border-radius: 10px; }}
    #ChipText {{ font-size: 12.5px; font-weight: 600; color: {T['text2']}; }}
    QLabel#SafeBadge {{ background: {SAFE_BG}; color: {SAFE}; border-radius: 999px;
        font-size: 11.5px; font-weight: 700; padding: 3px 9px; }}
    #Publisher {{ color: {T['text3']}; font-size: 11.5px; }}
    #Mono {{ font-family: 'JetBrains Mono','D2Coding',monospace; }}

    QScrollArea#License {{ background: {T['surfaceAlt']}; border: 1px solid {T['border']}; border-radius: 12px; }}
    QScrollArea#License QWidget {{ background: {T['surfaceAlt']}; }}
    #ArtTitle {{ font-size: 13.5px; font-weight: 700; }}
    #ArtBody {{ color: {T['text2']}; font-size: 12.5px; }}

    QLineEdit#Fld {{ background: #fff; border: 1.5px solid {T['borderStrong']}; border-radius: 10px;
        padding: 0 14px; min-height: 42px; font-size: 14px;
        font-family: 'JetBrains Mono','D2Coding',monospace; }}
    QLineEdit#Fld:focus {{ border-color: {b['brand']}; }}

    QPushButton#ChkCard {{ background: #fff; border: 1px solid {T['border']}; border-radius: 12px;
        text-align: left; padding: 13px 15px; }}
    QPushButton#ChkCard:hover {{ border-color: {T['borderStrong']}; }}
    QPushButton#ChkCard:checked {{ border: 1px solid {b['brand']}; background: {b['pink50']}; }}

    QFrame#Trust {{ background: {b['pink50']}; border: 1px solid #F6D2DE; border-radius: 10px; }}
    #TrustText {{ color: {b['ink']}; font-size: 12px; }}

    QPushButton#Primary {{ background: {b['brand']}; color: #fff; border: none; border-radius: 10px;
        min-height: 40px; padding: 0 18px; font-size: 13.5px; font-weight: 700; }}
    QPushButton#Primary:hover {{ background: {b['strong']}; }}
    QPushButton#Primary:pressed {{ background: {b['press']}; }}
    QPushButton#Primary:disabled {{ background: {b['pink200']}; color: #fff; }}
    QPushButton#Ghost {{ background: #fff; color: {T['text']}; border: 1px solid {T['borderStrong']};
        border-radius: 10px; min-height: 38px; padding: 0 16px; font-weight: 700; font-size: 13px; }}
    QPushButton#Ghost:hover {{ background: {T['surfaceAlt']}; }}
    QPushButton#Quiet {{ background: transparent; color: {T['text2']}; border: none;
        font-size: 12px; font-weight: 600; padding: 0 8px; }}
    QPushButton#Quiet:hover {{ color: {T['text']}; }}

    QProgressBar#Bar {{ border: none; border-radius: 8px; background: {T['surfaceAlt']}; height: 14px; }}
    QProgressBar#Bar::chunk {{ border-radius: 8px;
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {b['brand']}, stop:1 {b['strong']}); }}
    """


def _ic(name, size=18, color=T["text2"], stroke=2.0):
    lb = QLabel()
    lb.setPixmap(icons.line_icon(name, size, color, stroke))
    lb.setFixedSize(size, size)
    return lb


def _box_pixmap(on: bool, size: int = 20) -> QPixmap:
    """정본 Box(sq): 둥근 사각 체크박스. on이면 크림슨 채움 + 흰 체크."""
    pm = QPixmap(size, size); pm.fill(Qt.transparent)
    p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing, True)
    p.setPen(QPen(QColor(BRAND["brand"] if on else T["borderStrong"]), 1.7))
    p.setBrush(QColor(BRAND["brand"]) if on else QColor("#fff"))
    p.drawRoundedRect(1, 1, size - 2, size - 2, 6, 6)
    if on:
        p.drawPixmap(2, 2, icons.line_icon("check", size - 4, "#fff", 3))
    p.end()
    return pm


class _TbBtn(QPushButton):
    """창 제어 버튼(최소화/최대화/닫기) — 글리프를 직접 그린다."""

    def __init__(self, kind: str):
        super().__init__()
        self.kind = kind
        self.setObjectName("TbClose" if kind == "close" else "TbBtn")
        self.setProperty("class", "TbBtn")
        self.setFixedSize(42, 40)
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, e):
        super().paintEvent(e)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        hov = self.underMouse()
        col = "#fff" if (self.kind == "close" and hov) else T["text2"]
        pen = QPen(QColor(col))
        pen.setWidthF(1.2)
        p.setPen(pen)
        cx, cy = self.width() / 2, self.height() / 2
        if self.kind == "min":
            p.drawLine(int(cx - 5), int(cy), int(cx + 5), int(cy))
        elif self.kind == "max":
            p.drawRect(int(cx - 4), int(cy - 4), 8, 8)
        else:
            p.drawLine(int(cx - 4), int(cy - 4), int(cx + 4), int(cy + 4))
            p.drawLine(int(cx + 4), int(cy - 4), int(cx - 4), int(cy + 4))
        p.end()


class _Titlebar(QFrame):
    """드래그로 창 이동 가능한 타이틀바."""

    def __init__(self, win):
        super().__init__()
        self.setObjectName("Titlebar")
        self.setFixedHeight(40)
        self._win = win
        h = QHBoxLayout(self)
        h.setContentsMargins(13, 0, 6, 0)
        h.setSpacing(9)
        ic = QLabel()
        ic.setPixmap(icons.shield_pixmap(18, stroke=2, color="#fff", bg=BRAND["brand"]))
        h.addWidget(ic)
        title = QLabel("솔리가드 설치")
        title.setObjectName("TbTitle")
        h.addWidget(title)
        h.addStretch()
        b_min = _TbBtn("min"); b_min.clicked.connect(win.showMinimized)
        b_max = _TbBtn("max"); b_max.clicked.connect(win._toggle_max)
        b_cl = _TbBtn("close"); b_cl.clicked.connect(win.close)
        for b in (b_min, b_max, b_cl):
            h.addWidget(b)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            wh = self._win.windowHandle()
            if wh is not None:
                wh.startSystemMove()


class StepRow(QWidget):
    """레일 단계 한 줄: 번호 원 + 라벨. idle/active/done 상태."""

    def __init__(self, index: int, name: str):
        super().__init__()
        self.index = index
        h = QHBoxLayout(self)
        h.setContentsMargins(6, 8, 6, 8)
        h.setSpacing(11)
        self.num = QLabel(str(index + 1))
        self.num.setFixedSize(22, 22)
        self.num.setAlignment(Qt.AlignCenter)
        h.addWidget(self.num)
        self.lbl = QLabel(name)
        h.addWidget(self.lbl)
        h.addStretch()

    def set_state(self, state: str):
        if state == "active":
            self.num.setText(str(self.index + 1))
            self.num.setStyleSheet(
                f"background:#fff; color:{BRAND['brand']}; border-radius:11px;"
                "font-size:11px; font-weight:700;")
            self.lbl.setStyleSheet("color:#fff; font-size:13px; font-weight:700;")
        elif state == "done":
            self.num.setText("")
            self.num.setPixmap(icons.line_icon("check", 13, BRAND["brand"], 3))
            self.num.setStyleSheet(
                "background:rgba(255,255,255,0.92); border-radius:11px;")
            self.lbl.setStyleSheet("color:rgba(255,255,255,0.92); font-size:13px; font-weight:600;")
        else:
            self.num.setText(str(self.index + 1))
            self.num.setStyleSheet(
                "background:transparent; color:rgba(255,255,255,0.6);"
                "border:1.6px solid rgba(255,255,255,0.4); border-radius:11px;"
                "font-size:11px; font-weight:600;")
            self.lbl.setStyleSheet("color:rgba(255,255,255,0.6); font-size:13px; font-weight:600;")


class InstallerWizard(QWidget):
    finished_install = Signal(bool)  # run_now

    def __init__(self):
        super().__init__()
        self.fam = fonts.load_fonts(QApplication.instance())
        self.setWindowTitle("솔리가드 설치")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(760, 524)

        self.agree = False
        self.run_now = True
        self.opts = {"desktop": True, "startmenu": True, "autoscan": True, "ocr": True}
        self._index = 0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)  # 그림자 여백
        self.win = QFrame()
        self.win.setObjectName("Win")
        self.win.setStyleSheet(_qss(self.fam))
        sh = QGraphicsDropShadowEffect(self)
        sh.setBlurRadius(60); sh.setOffset(0, 18); sh.setColor(QColor(0, 0, 0, 120))
        self.win.setGraphicsEffect(sh)
        outer.addWidget(self.win)

        root = QVBoxLayout(self.win)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(_Titlebar(self))

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._build_rail())

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        self.stack = QStackedWidget()
        self.stack.addWidget(self._page_welcome())
        self.stack.addWidget(self._page_license())
        self.stack.addWidget(self._page_path())
        self.stack.addWidget(self._page_components())
        self.stack.addWidget(self._page_progress())
        self.stack.addWidget(self._page_done())
        right.addWidget(self.stack, 1)
        right.addWidget(self._build_foot())
        rw = QWidget(); rw.setLayout(right)
        body.addWidget(rw, 1)
        root.addLayout(body, 1)

        self._sync()

    def _toggle_max(self):
        self.showNormal() if self.isMaximized() else self.showMaximized()

    # ---------- 레일 ----------
    def _build_rail(self) -> QWidget:
        rail = QFrame()
        rail.setObjectName("Rail")
        rail.setFixedWidth(216)
        rail.setStyleSheet(
            "#Rail { background: qlineargradient(x1:0,y1:0,x2:0.7,y2:1,"
            "stop:0 #97103A, stop:0.6 #7E0C30, stop:1 #5E0A24); }")
        v = QVBoxLayout(rail)
        v.setContentsMargins(20, 24, 20, 18)
        v.setSpacing(0)

        brand = QLabel("솔리가드")
        brand.setObjectName("RailBrand")
        v.addWidget(brand)
        sub1 = QLabel("SoliGuard · solideo")
        sub1.setObjectName("RailSub")
        v.addWidget(sub1)
        v.addSpacing(10)
        sub2 = QLabel("SI 실무자 개인정보 점검 도구\n· v1.0.0")
        sub2.setObjectName("RailSub")
        v.addWidget(sub2)

        v.addSpacing(26)
        self.step_rows = []
        for i, name in enumerate(STEPS):
            r = StepRow(i, name)
            self.step_rows.append(r)
            v.addWidget(r)

        v.addStretch()
        foot = QWidget()
        fh = QHBoxLayout(foot); fh.setContentsMargins(0, 0, 0, 0); fh.setSpacing(7)
        fh.addWidget(_ic("shield", 13, "#FFFFFF", 2))
        ft = QLabel("로컬 전용 · 외부 전송 없음"); ft.setObjectName("RailFoot")
        fh.addWidget(ft); fh.addStretch()
        v.addWidget(foot)
        return rail

    # ---------- 페이지들 ----------
    def _content(self) -> tuple[QWidget, QVBoxLayout]:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(32, 30, 32, 30)
        v.setSpacing(0)
        return w, v

    def _page_welcome(self) -> QWidget:
        w, v = self._content()
        head = QHBoxLayout(); head.setSpacing(15)
        logo = QLabel()
        logo.setPixmap(icons.shield_pixmap(54, stroke=3, color="#fff", bg=BRAND["brand"]))
        head.addWidget(logo)
        hv = QVBoxLayout(); hv.setSpacing(6)
        t = QLabel("솔리가드 설치를 시작합니다"); t.setObjectName("Title")
        hv.addWidget(t)
        badge_row = QHBoxLayout(); badge_row.setSpacing(7)
        badge = QLabel("  디지털 서명 확인됨")
        badge.setObjectName("SafeBadge")
        badge.setPixmap(icons.line_icon("shieldCheck", 13, SAFE, 2.2))
        # 아이콘+텍스트 동시 표현이 어려워 텍스트 배지로 처리
        badge.setText("✓ 디지털 서명 확인됨")
        badge_row.addWidget(badge)
        pub = QLabel("게시자 solideo"); pub.setObjectName("Publisher")
        badge_row.addWidget(pub)
        badge_row.addStretch()
        hv.addLayout(badge_row)
        head.addLayout(hv); head.addStretch()
        v.addLayout(head)
        v.addSpacing(16)

        body = QLabel("설치형 도구로, 내 PC에 흩어진 개인정보·민감정보를 "
                      "<b>스캔·검출하고 마스킹·격리·삭제</b>합니다. "
                      "모든 작업은 <b>설치 PC 로컬</b>에서만 수행됩니다.")
        body.setObjectName("Body"); body.setWordWrap(True)
        v.addWidget(body)
        v.addSpacing(16)

        info = QFrame(); info.setObjectName("InfoBox")
        ih = QHBoxLayout(info); ih.setContentsMargins(18, 12, 18, 12); ih.setSpacing(0)
        for i, (cap, val, mono) in enumerate([
                ("버전", "1.0.0", True), ("설치 용량", "312 MB", True),
                ("지원 OS", "Windows 10 / 11", False)]):
            col = QVBoxLayout(); col.setSpacing(2)
            c = QLabel(cap); c.setStyleSheet(f"color:{T['text3']}; font-size:11px;")
            col.addWidget(c)
            x = QLabel(val)
            x.setStyleSheet("font-weight:700;" + (
                "font-family:'JetBrains Mono','D2Coding',monospace;" if mono else ""))
            col.addWidget(x)
            ih.addLayout(col, 14 if i == 2 else 10)
            if i < 2:
                sep = QFrame(); sep.setFixedWidth(1)
                sep.setStyleSheet(f"background:{T['border']};")
                ih.addSpacing(18); ih.addWidget(sep); ih.addSpacing(18)
        v.addWidget(info)
        v.addSpacing(16)

        chips = QHBoxLayout(); chips.setSpacing(9)
        for txt in ["한글(HWP) 2020 호환", "Tesseract 한국어 OCR 포함", "관리자 권한 필요"]:
            chip = QFrame(); chip.setObjectName("Chip")
            ch = QHBoxLayout(chip); ch.setContentsMargins(13, 8, 13, 8); ch.setSpacing(7)
            ch.addWidget(_ic("check", 14, SAFE, 2.6))
            cl = QLabel(txt); cl.setObjectName("ChipText")
            ch.addWidget(cl)
            chips.addWidget(chip)
        chips.addStretch()
        v.addLayout(chips)
        v.addStretch()
        return w

    def _page_license(self) -> QWidget:
        w, v = self._content()
        h2 = QLabel("사용권 계약"); h2.setObjectName("H2")
        v.addWidget(h2); v.addSpacing(14)

        arts = [
            ("제1조 (목적)", "본 소프트웨어는 SI 사업장 실무자가 PC 내 개인정보·민감정보를 "
                          "스스로 점검·조치하기 위한 내부 업무용 도구입니다."),
            ("제2조 (데이터 처리)", "검출된 모든 데이터와 생성된 리포트는 설치된 PC 로컬 저장소에만 "
                              "보관되며, 외부 서버로 전송되지 않습니다."),
            ("제3조 (필수 구성요소)", "본 도구는 한글(HWP) 파서 및 Tesseract 한국어 OCR 런타임이 "
                               "설치된 환경에서 동작합니다."),
        ]
        area = QScrollArea(); area.setObjectName("License")
        area.setWidgetResizable(True)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        inner = QWidget(); iv = QVBoxLayout(inner)
        iv.setContentsMargins(18, 16, 18, 16); iv.setSpacing(14)
        for t, d in arts:
            box = QVBoxLayout(); box.setSpacing(3)
            at = QLabel(t); at.setObjectName("ArtTitle")
            box.addWidget(at)
            ad = QLabel(d); ad.setObjectName("ArtBody"); ad.setWordWrap(True)
            box.addWidget(ad)
            iv.addLayout(box)
        iv.addStretch()
        area.setWidget(inner)
        v.addWidget(area, 1)
        v.addSpacing(14)

        self.agree_btn = self._check_card("위 사용권 계약에 동의합니다.", False, self._on_agree)
        v.addWidget(self.agree_btn)
        return w

    def _check_card(self, text, checked, slot) -> QPushButton:
        """체크박스 사각 + 라벨 카드(정본 chk-card)."""
        b = QPushButton(); b.setObjectName("ChkCard")
        b.setCheckable(True); b.setChecked(checked)
        b.setCursor(Qt.PointingHandCursor); b.setMinimumHeight(48)
        h = QHBoxLayout(b); h.setContentsMargins(15, 12, 15, 12); h.setSpacing(12)
        box = QLabel(); box.setFixedSize(20, 20); box.setPixmap(_box_pixmap(checked))
        h.addWidget(box)
        lab = QLabel(text); lab.setStyleSheet("font-size:13.5px; font-weight:700;")
        h.addWidget(lab); h.addStretch()
        b.toggled.connect(lambda on: (box.setPixmap(_box_pixmap(on)), slot(on)))
        return b

    def _on_agree(self, on: bool):
        self.agree = on
        self.next_btn.setEnabled(on)

    def _page_path(self) -> QWidget:
        w, v = self._content()
        h2 = QLabel("설치 위치"); h2.setObjectName("H2")
        v.addWidget(h2); v.addSpacing(6)
        sub = QLabel("솔리가드를 설치할 폴더를 선택하세요."); sub.setObjectName("Sub")
        v.addWidget(sub); v.addSpacing(18)
        lab = QLabel("설치 폴더")
        lab.setStyleSheet(f"font-size:12.5px; font-weight:600; color:{T['text2']};")
        v.addWidget(lab); v.addSpacing(7)
        row = QHBoxLayout(); row.setSpacing(8)
        self.path_edit = QLineEdit(r"C:\Program Files\SoliGuard")
        self.path_edit.setObjectName("Fld")
        row.addWidget(self.path_edit, 1)
        browse = QPushButton("  찾아보기"); browse.setObjectName("Ghost")
        browse.setCursor(Qt.PointingHandCursor)
        browse.clicked.connect(self._browse)
        row.addWidget(browse)
        v.addLayout(row); v.addSpacing(20)
        meta = QHBoxLayout(); meta.setSpacing(20)
        for cap, val in [("필요 공간", "312 MB"), ("사용 가능", "84.6 GB")]:
            cell = QLabel(
                f"<span style='color:{T['text3']}'>{cap}</span> "
                f"<b style=\"font-family:'JetBrains Mono',monospace\">{val}</b>")
            cell.setStyleSheet("font-size:12.5px;")
            meta.addWidget(cell)
        meta.addStretch()
        v.addLayout(meta)
        v.addStretch()
        return w

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "설치 폴더 선택", "C:\\")
        if d:
            self.path_edit.setText(d.replace("/", "\\"))

    def _page_components(self) -> QWidget:
        w, v = self._content()
        h2 = QLabel("구성요소 선택"); h2.setObjectName("H2")
        v.addWidget(h2); v.addSpacing(6)
        sub = QLabel("설치할 항목을 선택하세요."); sub.setObjectName("Sub")
        v.addWidget(sub); v.addSpacing(16)
        items = [
            ("desktop", "folder", "바탕화면 아이콘 생성", "바탕화면에 솔리가드 바로가기를 만듭니다"),
            ("startmenu", "home", "시작 메뉴 바로가기 등록", "시작 메뉴에서 빠르게 실행할 수 있습니다"),
            ("autoscan", "clock", "주 1회 자동 점검 사용 (권장)", "매주 월요일 09:00, 작업 스케줄러에 등록됩니다"),
            ("ocr", "image", "Tesseract 한국어 OCR 포함", "이미지 속 신분증·계약서 검사에 필요합니다"),
        ]
        col = QVBoxLayout(); col.setSpacing(9)
        self.opt_btns = {}
        for key, ic, t1, t2 in items:
            col.addWidget(self._opt_card(key, ic, t1, t2))
        v.addLayout(col); v.addSpacing(14)
        trust = QFrame(); trust.setObjectName("Trust")
        th = QHBoxLayout(trust); th.setContentsMargins(14, 12, 14, 12); th.setSpacing(9)
        th.addWidget(_ic("shield", 15, BRAND["ink"], 2))
        tl = QLabel("설치 시 관리자 권한(UAC) 요청 창이 나타나면 “예”를 눌러 진행하세요.")
        tl.setObjectName("TrustText"); tl.setWordWrap(True)
        th.addWidget(tl, 1)
        v.addWidget(trust)
        v.addStretch()
        return w

    def _opt_card(self, key, ic, t1, t2) -> QPushButton:
        b = QPushButton(); b.setObjectName("ChkCard")
        b.setCheckable(True); b.setChecked(self.opts[key])
        b.setCursor(Qt.PointingHandCursor)
        h = QHBoxLayout(b); h.setContentsMargins(15, 11, 15, 11); h.setSpacing(12)
        box = QLabel(); box.setFixedSize(20, 20)
        box.setPixmap(_box_pixmap(self.opts[key]))
        h.addWidget(box)
        ic_lab = _ic(ic, 18, BRAND["brand"] if self.opts[key] else T["text3"], 2)
        h.addWidget(ic_lab)
        tv = QVBoxLayout(); tv.setSpacing(1)
        l1 = QLabel(t1); l1.setStyleSheet("font-size:13.5px; font-weight:700;")
        tv.addWidget(l1)
        l2 = QLabel(t2); l2.setStyleSheet(f"font-size:12px; color:{T['text2']};")
        tv.addWidget(l2)
        h.addLayout(tv, 1)

        def on_toggle(on, k=key, bx=box, icl=ic_lab, ico=ic):
            self.opts[k] = on
            bx.setPixmap(_box_pixmap(on))
            icl.setPixmap(icons.line_icon(ico, 18, BRAND["brand"] if on else T["text3"], 2))
        b.toggled.connect(on_toggle)
        self.opt_btns[key] = b
        return b

    def _page_progress(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(32, 30, 32, 30)
        v.setSpacing(0)
        v.addStretch()
        h2 = QLabel("설치 중…"); h2.setObjectName("H2")
        v.addWidget(h2); v.addSpacing(6)
        self.prog_line = QLabel("파일 압축 해제 중...")
        self.prog_line.setObjectName("Mono")
        self.prog_line.setStyleSheet(f"color:{T['text2']}; font-size:12.5px;"
                                     "font-family:'JetBrains Mono','D2Coding',monospace;")
        v.addWidget(self.prog_line); v.addSpacing(16)
        prow = QHBoxLayout()
        pl = QLabel("진행률"); pl.setStyleSheet(f"color:{T['text3']}; font-size:12.5px;")
        prow.addWidget(pl); prow.addStretch()
        self.pct_label = QLabel("0%")
        self.pct_label.setStyleSheet(
            f"color:{BRAND['brand']}; font-weight:800; font-size:24px;"
            "font-family:'JetBrains Mono','D2Coding',monospace;")
        prow.addWidget(self.pct_label)
        v.addLayout(prow); v.addSpacing(8)
        self.bar = QProgressBar(); self.bar.setObjectName("Bar")
        self.bar.setRange(0, 100); self.bar.setValue(0); self.bar.setTextVisible(False)
        self.bar.setFixedHeight(14)
        v.addWidget(self.bar)
        v.addStretch()
        return w

    def _page_done(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(32, 30, 32, 30)
        v.setSpacing(0)
        v.addStretch()
        badge = QLabel()
        badge.setFixedSize(64, 64)
        badge.setAlignment(Qt.AlignCenter)
        pm = QPixmap(64, 64); pm.fill(Qt.transparent)
        p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing, True)
        p.setPen(Qt.NoPen); p.setBrush(QColor(SAFE_BG)); p.drawEllipse(0, 0, 64, 64)
        p.end()
        badge.setPixmap(pm)
        # 체크 아이콘 겹쳐 그리기
        comp = QPixmap(64, 64); comp.fill(Qt.transparent)
        p2 = QPainter(comp); p2.setRenderHint(QPainter.Antialiasing, True)
        p2.drawPixmap(0, 0, pm)
        chk = icons.line_icon("check", 34, SAFE, 2.6)
        p2.drawPixmap(15, 15, chk)
        p2.end()
        badge.setPixmap(comp)
        v.addWidget(badge); v.addSpacing(16)
        t = QLabel("설치가 완료되었습니다"); t.setObjectName("Title")
        v.addWidget(t); v.addSpacing(8)
        body = QLabel("솔리가드가 설치되었습니다. 처음 실행하면 직무에 맞춘 초기 설정을 안내합니다.")
        body.setObjectName("Body"); body.setWordWrap(True)
        v.addWidget(body); v.addSpacing(18)
        self.run_btn = self._check_card("지금 솔리가드 실행", True,
                                        lambda on: setattr(self, "run_now", on))
        self.run_btn.setMaximumWidth(360)
        v.addWidget(self.run_btn)
        v.addStretch()
        return w

    # ---------- 푸터 ----------
    def _build_foot(self) -> QWidget:
        foot = QFrame(); foot.setObjectName("Foot")
        h = QHBoxLayout(foot); h.setContentsMargins(24, 14, 24, 14); h.setSpacing(10)
        self.step_tag = QLabel("단계 1 / 6"); self.step_tag.setObjectName("StepTag")
        h.addWidget(self.step_tag)
        self.cancel_btn = QPushButton("취소"); self.cancel_btn.setObjectName("Quiet")
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.close)
        h.addWidget(self.cancel_btn)
        h.addStretch()
        self.back_btn = QPushButton("  이전"); self.back_btn.setObjectName("Ghost")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.clicked.connect(self._prev)
        h.addWidget(self.back_btn)
        self.next_btn = QPushButton("다음  "); self.next_btn.setObjectName("Primary")
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.clicked.connect(self._next)
        h.addWidget(self.next_btn)
        self.foot = foot
        return foot

    # ---------- 네비게이션 ----------
    def _sync(self):
        self.stack.setCurrentIndex(self._index)
        for i, r in enumerate(self.step_rows):
            r.set_state("active" if i == self._index else "done" if i < self._index else "idle")
        self.step_tag.setText(f"단계 {min(self._index + 1, 6)} / 6")
        # 푸터 표시: 설치 진행(4) 단계는 숨김
        self.foot.setVisible(self._index != 4)
        self.cancel_btn.setVisible(self._index < 5)
        self.back_btn.setVisible(0 < self._index < 5)
        if self._index == 5:
            self.next_btn.setText("  마침")
            self.next_btn.setIcon(self._icon("check"))
        elif self._index == 3:
            self.next_btn.setText("설치 시작  ")
        else:
            self.next_btn.setText("다음  ")
        self.next_btn.setVisible(self._index != 4)
        self.next_btn.setEnabled(not (self._index == 1 and not self.agree))

    def _icon(self, name):
        from PySide6.QtGui import QIcon
        return QIcon(icons.line_icon(name, 16, "#fff", 2.4))

    def _next(self):
        if self._index == 5:
            self.finished_install.emit(self.run_now)
            self.close()
            return
        if self._index == 3:  # 구성요소 → 설치 진행
            self._index = 4
            self._sync()
            self._start_progress()
            return
        self._index = min(5, self._index + 1)
        self._sync()

    def _prev(self):
        self._index = max(0, self._index - 1)
        self._sync()

    def _start_progress(self):
        lines = ["파일 압축 해제 중...",
                 "검출 엔진 설치 (detectors · scanner · engine)",
                 "한글(HWP) 파서 구성요소 등록"]
        if self.opts["ocr"]:
            lines.append("Tesseract 한국어 OCR 데이터 배치")
        if self.opts["desktop"]:
            lines.append("바탕화면 바로가기 생성")
        if self.opts["startmenu"]:
            lines.append("시작 메뉴 등록")
        if self.opts["autoscan"]:
            lines.append("작업 스케줄러에 주간 점검(월 09:00) 등록")
        lines.append("설치 마무리 중...")
        self._lines = lines
        self._pct = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(34)

    def _tick(self):
        self._pct = min(100, self._pct + 2)
        self.bar.setValue(self._pct)
        self.pct_label.setText(f"{self._pct}%")
        li = min(len(self._lines) - 1, self._pct * len(self._lines) // 100)
        self.prog_line.setText(self._lines[li])
        if self._pct >= 100:
            self._timer.stop()
            QTimer.singleShot(400, self._goto_done)

    def _goto_done(self):
        self._index = 5
        self._sync()


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    fonts.load_fonts(app)
    app.setWindowIcon(icons.app_icon())
    wiz = InstallerWizard()
    _refs = {}

    def on_done(run_now: bool):
        if run_now:
            from .app import SoliGuardApp
            _refs["app"] = SoliGuardApp()
        else:
            app.quit()

    wiz.finished_install.connect(on_done)
    wiz.show()
    import os
    shot = os.environ.get("SOLIGUARD_SHOT")
    if shot:
        def _grab():
            wiz.grab().save(shot)
            print("SHOT installer", wiz.fam)
            app.quit()
        QTimer.singleShot(450, _grab)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
