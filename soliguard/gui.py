"""PySide6 GUI - 정본(docs/app) 디자인 반영.

흰 사이드바(로고·메뉴·직무 칩) + 콘텐츠(대시보드/스캔/결과/격리함/이력/설정).
결과 화면은 좌측 위험도 필터 · 중앙 표(위험도 칩) · 우측 마스킹 미리보기 3분할.
스캔은 별도 스레드(ScanWorker)에서 실행.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QComboBox, QDialog, QFileDialog,
    QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QHeaderView, QInputDialog,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QProgressBar, QPushButton,
    QStackedWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)
from PySide6.QtGui import QColor

from . import fonts, icons
from .engine import PROFILE_ROLE, run_scan
from .profiles import ALL_PROFILES, PROFILE_DESC, PROFILE_ICON
from .report import ReportError, generate_pdf_report
from .theme import BRAND, GRADE_DISPLAY, SEMANTIC, SEV_CHIP, build_qss

_FREQ_ITEMS = ["사용 안 함", "매일", "매주(월요일)", "매월(1일)"]
_ACTION_KO = {"mask": "마스킹", "quarantine": "격리", "restore": "복원",
              "delete": "완전삭제", "figma_scan": "Figma 검사"}


# ---------------------------------------------------------------- 공용 위젯
def _h1(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet("font-size:23px; font-weight:800;")
    return lbl


def _card(shadow: bool = True) -> QFrame:
    f = QFrame()
    f.setObjectName("Card")
    if shadow:
        eff = QGraphicsDropShadowEffect(f)
        eff.setBlurRadius(20)
        eff.setOffset(0, 3)
        eff.setColor(QColor(16, 18, 24, 16))
        f.setGraphicsEffect(eff)
    return f


def _sev_chip(sev_value: str) -> QWidget:
    color, bg, line = SEV_CHIP.get(sev_value, ("#8B92A0", "#F1F2F4", "#E7E9EE"))
    wrap = QWidget()
    h = QHBoxLayout(wrap)
    h.setContentsMargins(0, 0, 0, 0)
    chip = QLabel("● " + sev_value)
    chip.setStyleSheet(
        f"background:{bg}; color:{color}; border:1px solid {line};"
        f"border-radius:10px; padding:2px 9px; font-weight:700; font-size:11px;")
    h.addWidget(chip)
    h.addStretch()
    return wrap


class DonutHero(QWidget):
    """위험 항목 도넛 게이지(높음/중간/낮음 비율 + 가운데 총건수)."""

    def __init__(self):
        super().__init__()
        self.setFixedSize(200, 200)
        self.counts = {"높음": 0, "중간": 0, "낮음": 0}
        self.grade = "안전"

    def set_data(self, counts: dict, grade: str):
        self.counts = counts
        self.grade = grade
        self.update()

    def paintEvent(self, _e):
        from PySide6.QtGui import QPainter, QPen
        from PySide6.QtCore import QRectF

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        rect = QRectF(22, 22, 156, 156)
        total = sum(self.counts.values())
        pen = QPen()
        pen.setWidth(18)
        pen.setCapStyle(Qt.RoundCap)
        # 트랙
        pen.setColor(QColor("#EFF1F4"))
        p.setPen(pen)
        p.drawArc(rect, 0, 360 * 16)
        if total:
            start = 90 * 16
            for sev in ("높음", "중간", "낮음"):
                v = self.counts.get(sev, 0)
                if not v:
                    continue
                span = -int(360 * 16 * v / total)
                pen.setColor(QColor(SEV_CHIP[sev][0]))
                p.setPen(pen)
                p.drawArc(rect, start, span)
                start += span
        # 가운데 텍스트
        from .theme import grade_color
        p.setPen(QColor(grade_color(self.grade)))
        f = self.font(); f.setPointSize(11); f.setBold(True); p.setFont(f)
        p.drawText(QRectF(0, 64, 200, 20), Qt.AlignCenter, self.grade)
        p.setPen(QColor("#14161C"))
        f.setPointSize(34); p.setFont(f)
        p.drawText(QRectF(0, 80, 200, 46), Qt.AlignCenter, str(total))
        p.setPen(QColor("#565E6C"))
        f.setPointSize(9); f.setBold(False); p.setFont(f)
        p.drawText(QRectF(0, 128, 200, 18), Qt.AlignCenter, "위험 항목")
        p.end()


def _mini_stat(icon: str, label: str, value: str) -> QWidget:
    w = QWidget()
    h = QHBoxLayout(w)
    h.setContentsMargins(0, 0, 0, 0)
    h.setSpacing(9)
    av = QLabel(icon)
    av.setFixedSize(32, 32)
    av.setAlignment(Qt.AlignCenter)
    av.setStyleSheet("background:#F7F8FA; border-radius:8px; font-size:15px;")
    h.addWidget(av)
    col = QVBoxLayout()
    col.setSpacing(0)
    l1 = QLabel(label); l1.setStyleSheet("font-size:11px; color:#8B92A0;")
    col.addWidget(l1)
    l2 = QLabel(value); l2.setStyleSheet("font-size:13px; font-weight:700;")
    col.addWidget(l2)
    h.addLayout(col)
    w._value_label = l2
    return w


# ---------------------------------------------------------------- 스캔 워커
def _bucket_of(info_type: str) -> str:
    if info_type in ("주민등록번호", "외국인등록번호", "신분증 이미지", "실고객 샘플"):
        return "주민등록번호"
    if info_type == "신용카드번호":
        return "신용카드번호"
    if info_type in ("API 키/시크릿", "DB 접속정보", "AWS Access Key", "개인키(PEM)"):
        return "API키/DB"
    if info_type in ("전화번호", "이메일"):
        return "전화·이메일"
    return "기타"


class ScanWorker(QThread):
    progress = Signal(int, int, str, dict)   # done, total, path, bucket_counts
    finished_scan = Signal(object)

    def __init__(self, folders, profiles, ocr_enabled, user_whitelist=None):
        super().__init__()
        self.folders = folders
        self.profiles = list(profiles)
        self.ocr_enabled = ocr_enabled
        self.user_whitelist = list(user_whitelist or [])
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        from .detection import DetectionEngine
        from .engine import DEFAULT_EXCLUDES, PROFILE_ROLE, ScanSummary
        from .scanner import collect_files, scan_file

        roles = {PROFILE_ROLE[p] for p in self.profiles if p in PROFILE_ROLE}
        engine = DetectionEngine(roles=roles or None, user_whitelist=self.user_whitelist)
        files = collect_files(self.folders, exclude=DEFAULT_EXCLUDES)
        total = len(files)
        results, scanned, skipped = [], 0, 0
        buckets = {"주민등록번호": 0, "신용카드번호": 0, "API키/DB": 0,
                   "전화·이메일": 0, "기타": 0}
        for i, fpath in enumerate(files, 1):
            if self._stop:
                break
            r = scan_file(fpath, engine, ocr_enabled=self.ocr_enabled)
            results.append(r)
            if r.status == "검사불가":
                skipped += 1
            else:
                scanned += 1
                for f in r.findings:
                    buckets[_bucket_of(f.info_type)] += 1
            self.progress.emit(i, total, str(fpath), dict(buckets))
        self.finished_scan.emit(ScanSummary(file_results=results, scanned=scanned, skipped=skipped))


# ---------------------------------------------------------------- 직무 팝오버
class RolePopover(QDialog):
    """직무 프로파일 복수 선택 다이얼로그(사이드바 칩에서 호출)."""

    def __init__(self, parent, profiles):
        super().__init__(parent)
        self.setWindowTitle("직무 프로파일")
        self.setModal(True)
        self.setMinimumWidth(380)
        self.selected = list(profiles)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 14)
        lay.setSpacing(8)
        title = QLabel("직무 프로파일  (복수 선택)")
        title.setStyleSheet("font-size:15px; font-weight:800;")
        lay.addWidget(title)
        hint = QLabel("선택한 모든 직무의 폴더·검출 항목이 합쳐서 구성됩니다.")
        hint.setStyleSheet("color:#565E6C; font-size:12px;")
        lay.addWidget(hint)

        self._checks = {}
        for role in ALL_PROFILES:
            row = QFrame()
            row.setObjectName("Card")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(12, 9, 12, 9)
            icon = QLabel(PROFILE_ICON.get(role, "•"))
            icon.setStyleSheet("font-size:18px;")
            rl.addWidget(icon)
            col = QVBoxLayout()
            col.setSpacing(1)
            nm = QLabel(role)
            nm.setStyleSheet("font-weight:700; font-size:13.5px;")
            col.addWidget(nm)
            ds = QLabel(PROFILE_DESC.get(role, ""))
            ds.setStyleSheet("color:#565E6C; font-size:12px;")
            ds.setWordWrap(True)
            col.addWidget(ds)
            rl.addLayout(col, 1)
            chk = QCheckBox()
            chk.setChecked(role in self.selected)
            rl.addWidget(chk)
            self._checks[role] = chk
            lay.addWidget(row)

        foot = QHBoxLayout()
        self._count = QLabel()
        self._count.setStyleSheet("color:#8B92A0; font-size:12px;")
        foot.addWidget(self._count)
        foot.addStretch()
        apply_btn = QPushButton("적용")
        apply_btn.setObjectName("Primary")
        apply_btn.clicked.connect(self._apply)
        foot.addWidget(apply_btn)
        lay.addLayout(foot)
        for c in self._checks.values():
            c.toggled.connect(self._refresh_count)
        self._refresh_count()

    def _refresh_count(self):
        n = sum(1 for c in self._checks.values() if c.isChecked())
        self._count.setText(f"{n}개 직무 선택됨")

    def _apply(self):
        sel = [r for r in ALL_PROFILES if self._checks[r].isChecked()]
        self.selected = sel or [ALL_PROFILES[0]]
        self.accept()


# ---------------------------------------------------------------- 메인 윈도우
class MainWindow(QMainWindow):
    scan_finished = Signal(str)

    def __init__(self, cfg=None):
        super().__init__()
        self.setWindowTitle("SoliGuard")
        self.setWindowIcon(icons.app_icon())
        self.resize(1180, 760)
        self.cfg = cfg
        self.profile = getattr(cfg, "profile", None) or "개발자"
        self.profiles = list(getattr(cfg, "profiles", None) or [self.profile])
        self.worker = None
        self.file_results = []
        self.row_index = []
        self._tray_active = False
        self._closing_mode = False

        root = QWidget()
        row = QHBoxLayout(root)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addWidget(self._build_sidebar())
        self.stack = QStackedWidget()
        self.dashboard = self._build_dashboard()
        self.scanning = self._build_scanning()
        self.scanconfig = self._build_scanconfig()
        self.results = self._build_results()
        self.quarantine = self._build_quarantine()
        self.history = self._build_history()
        self.settings = self._build_settings()
        for wdg in (self.dashboard, self.scanning, self.scanconfig, self.results,
                    self.quarantine, self.history, self.settings):
            self.stack.addWidget(wdg)
        row.addWidget(self.stack, 1)
        self.setCentralWidget(root)
        self.stack.setCurrentWidget(self.dashboard)

    # -------------------------------------------------------- 사이드바
    def _build_sidebar(self) -> QWidget:
        side = QWidget()
        side.setObjectName("Sidebar")
        side.setFixedWidth(232)
        lay = QVBoxLayout(side)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # 브랜드
        brand = QWidget()
        bl = QHBoxLayout(brand)
        bl.setContentsMargins(18, 20, 18, 16)
        bl.setSpacing(11)
        logo = QLabel()
        logo.setFixedSize(34, 34)
        logo.setPixmap(icons.shield_pixmap(34, stroke=2, color="#FFFFFF", bg=BRAND["brand"]))
        bl.addWidget(logo)
        nm = QVBoxLayout()
        nm.setSpacing(0)
        name = QLabel('솔리<span style="color:%s;font-weight:800;">가드</span>' % BRAND["brand"])
        name.setStyleSheet("font-size:16px; font-weight:800;")
        nm.addWidget(name)
        tag = QLabel("SoliGuard · v" + getattr(__import__("soliguard"), "__version__", "1.0"))
        tag.setStyleSheet("font-size:10.5px; color:#8B92A0;")
        nm.addWidget(tag)
        bl.addLayout(nm)
        bl.addStretch()
        lay.addWidget(brand)

        sec = QLabel("메뉴")
        sec.setStyleSheet("font-size:10.5px; font-weight:700; color:#8B92A0; padding:6px 22px 7px;")
        lay.addWidget(sec)

        self.nav_group = QButtonGroup(self)
        self._nav_buttons = {}
        navwrap = QWidget()
        nv = QVBoxLayout(navwrap)
        nv.setContentsMargins(12, 0, 12, 0)
        nv.setSpacing(2)
        for key, label in [("dashboard", "  홈"), ("quarantine", "  격리함"),
                           ("history", "  점검 이력"), ("settings", "  설정")]:
            b = QPushButton(label)
            b.setObjectName("Nav")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, k=key: self._navigate(k))
            self.nav_group.addButton(b)
            self._nav_buttons[key] = b
            nv.addWidget(b)
        self._nav_buttons["dashboard"].setChecked(True)
        lay.addWidget(navwrap)

        lay.addStretch()

        trust = QLabel("🔒  데이터는 이 PC 안에서만 처리됩니다")
        trust.setStyleSheet("color:#8B92A0; font-size:11px; padding:8px 16px 4px;")
        lay.addWidget(trust)

        # 직무 칩
        chip = QFrame()
        chip.setObjectName("RoleChip")
        cl = QHBoxLayout(chip)
        cl.setContentsMargins(12, 9, 12, 9)
        av = QLabel(PROFILE_ICON.get(self.profiles[0], "•"))
        av.setFixedSize(30, 30)
        av.setAlignment(Qt.AlignCenter)
        av.setStyleSheet(f"background:{BRAND['pink100']}; color:{BRAND['brand']}; border-radius:8px; font-size:15px;")
        cl.addWidget(av)
        rc = QVBoxLayout()
        rc.setSpacing(0)
        self._role_caption = QLabel()
        self._role_caption.setStyleSheet("font-size:10.5px; color:#8B92A0;")
        rc.addWidget(self._role_caption)
        self._role_value = QLabel()
        self._role_value.setStyleSheet("font-size:13px; font-weight:700;")
        rc.addWidget(self._role_value)
        cl.addLayout(rc, 1)
        cl.addWidget(QLabel("›"))
        btn = QPushButton(chip)  # 투명 클릭 영역
        btn.setStyleSheet("background:transparent; border:none;")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self._open_role_popover)
        chip.mousePressEvent = lambda e: self._open_role_popover()
        wrap = QWidget()
        wl = QVBoxLayout(wrap)
        wl.setContentsMargins(12, 4, 12, 12)
        wl.addWidget(chip)
        lay.addWidget(wrap)
        self._refresh_role_chip()
        return side

    def _refresh_role_chip(self):
        n = len(self.profiles)
        self._role_caption.setText("직무 프로파일" + (f" · {n}개" if n > 1 else ""))
        self._role_value.setText(", ".join(self.profiles))

    def _open_role_popover(self):
        dlg = RolePopover(self, self.profiles)
        if dlg.exec() == QDialog.Accepted:
            self.profiles = dlg.selected
            self.profile = self.profiles[0]
            self._refresh_role_chip()

    def _navigate(self, key: str):
        target = {"dashboard": self.dashboard, "quarantine": self.quarantine,
                  "history": self.history, "settings": self.settings}[key]
        if key == "quarantine":
            self._refresh_quarantine()
        elif key == "history":
            self._refresh_history()
        elif key == "settings" and hasattr(self, "font_info_label"):
            # 실제 렌더 폰트(fontInfo)를 표시 — 사용자가 직접 확인 가능
            self.font_info_label.setText(
                "현재 글꼴: " + self.font_info_label.fontInfo().family())
        self.stack.setCurrentWidget(target)

    def _select_nav(self, key: str):
        self._nav_buttons[key].setChecked(True)

    # -------------------------------------------------------- 대시보드
    def _build_dashboard(self) -> QWidget:
        outer = QWidget()
        ol = QVBoxLayout(outer)
        ol.setContentsMargins(32, 28, 32, 28)
        ol.setSpacing(18)
        ph = QLabel("보안 대시보드")
        ph.setStyleSheet("font-size:23px; font-weight:800;")
        ol.addWidget(ph)
        self.dash_sub = QLabel("아직 점검 기록이 없습니다 — 첫 점검을 시작해 보세요")
        self.dash_sub.setStyleSheet("color:#565E6C; font-size:13px;")
        ol.addWidget(self.dash_sub)

        # 히어로 카드
        hero = _card()
        hl = QHBoxLayout(hero)
        hl.setContentsMargins(26, 22, 26, 22)
        hl.setSpacing(28)
        self.donut = DonutHero()
        hl.addWidget(self.donut)

        right = QVBoxLayout()
        right.setSpacing(8)
        gr = QHBoxLayout()
        gt = QLabel("내 PC 개인정보 위험 등급")
        gt.setStyleSheet("font-size:18px; font-weight:800;")
        gr.addWidget(gt)
        self.grade_chip_label = QLabel("미점검")
        self._style_sev_label(self.grade_chip_label, None)
        gr.addWidget(self.grade_chip_label)
        gr.addStretch()
        right.addLayout(gr)
        self.grade_label = QLabel("점검을 시작하면 위험 등급이 표시됩니다.")
        self.grade_label.setWordWrap(True)
        self.grade_label.setStyleSheet("color:#565E6C; font-size:13.5px;")
        right.addWidget(self.grade_label)
        btns = QHBoxLayout()
        scan_btn = QPushButton("🔍  지금 점검하기")
        scan_btn.setObjectName("Primary")
        scan_btn.setMinimumHeight(46)
        scan_btn.setCursor(Qt.PointingHandCursor)
        scan_btn.clicked.connect(lambda: self._go_scanconfig("full"))
        btns.addWidget(scan_btn)
        quick_btn = QPushButton("⚡  빠른 점검")
        quick_btn.setObjectName("Ghost")
        quick_btn.setMinimumHeight(46)
        quick_btn.clicked.connect(lambda: self._go_scanconfig("quick"))
        btns.addWidget(quick_btn)
        btns.addStretch()
        right.addSpacing(6)
        right.addLayout(btns)
        stats = QHBoxLayout()
        stats.setSpacing(18)
        self.stat_next = _mini_stat("⏰", "다음 자동 점검", "사용 안 함")
        self.stat_role = _mini_stat("📁", "점검 직무", ", ".join(self.profiles))
        self.stat_quar = _mini_stat("🗄", "격리 보관", "0개")
        stats.addWidget(self.stat_next)
        stats.addWidget(self.stat_role)
        stats.addWidget(self.stat_quar)
        stats.addStretch()
        right.addSpacing(8)
        right.addLayout(stats)
        hl.addLayout(right, 1)
        ol.addWidget(hero)

        # 하단: 최근활동 + 클로징
        low = QHBoxLayout()
        low.setSpacing(18)
        recent = _card()
        rl = QVBoxLayout(recent)
        rl.setContentsMargins(22, 18, 22, 18)
        rhead = QHBoxLayout()
        rt = QLabel("최근 활동")
        rt.setStyleSheet("font-size:15px; font-weight:800;")
        rhead.addWidget(rt)
        rhead.addStretch()
        allbtn = QPushButton("전체 보기 ›")
        allbtn.setStyleSheet("background:transparent; border:none; color:#565E6C; font-size:12px;")
        allbtn.setCursor(Qt.PointingHandCursor)
        allbtn.clicked.connect(lambda: self._nav_buttons["history"].click())
        rhead.addWidget(allbtn)
        rl.addLayout(rhead)
        self.recent_box = QVBoxLayout()
        rl.addLayout(self.recent_box)
        self._render_recent()
        rl.addStretch()
        low.addWidget(recent, 3)

        closing = _card()
        cc = QVBoxLayout(closing)
        cc.setContentsMargins(22, 18, 22, 18)
        ct = QLabel("프로젝트 클로징 점검")
        ct.setStyleSheet("font-size:15px; font-weight:800;")
        cc.addWidget(ct)
        cd = QLabel("프로젝트가 끝나면 잔여 발주처 데이터를 한 번에 정리하고 진단서를 발급하세요.")
        cd.setWordWrap(True)
        cd.setStyleSheet("color:#565E6C; font-size:13px;")
        cc.addWidget(cd)
        trust = QLabel("프로젝트가 끝나면, 데이터도 깨끗하게. 검출된 데이터는 외부로 전송되지 않습니다.")
        trust.setWordWrap(True)
        trust.setObjectName("Card")
        trust.setStyleSheet("background:#FCEFF3; border:1px solid #F6D2DE; border-radius:10px; color:#5E0A24; font-size:12px; padding:12px;")
        cc.addStretch()
        cc.addWidget(trust)
        cbtn = QPushButton("📁  클로징 점검 시작")
        cbtn.setObjectName("Ghost")
        cbtn.clicked.connect(lambda: self._go_scanconfig("closing"))
        cc.addWidget(cbtn)
        low.addWidget(closing, 2)
        ol.addLayout(low, 1)
        return outer

    def _render_recent(self):
        while self.recent_box.count():
            it = self.recent_box.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        entries = _read_audit_tail(6)
        if not entries:
            e = QLabel("아직 점검 이력이 없습니다. ‘지금 점검하기’로 첫 점검을 시작하세요.")
            e.setStyleSheet("color:#8B92A0; padding:8px 0;")
            self.recent_box.addWidget(e)
            return
        for e in entries:
            lbl = QLabel(f"·  {e.get('ts','')}   {_ACTION_KO.get(e.get('action',''), e.get('action',''))}"
                         f"   {Path(e.get('path','')).name}   [{e.get('result','')}]")
            lbl.setStyleSheet("color:#565E6C; padding:3px 0;")
            self.recent_box.addWidget(lbl)

    # -------------------------------------------------------- 스캔 진행
    def _build_scanning(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(36, 28, 36, 28)
        lay.setSpacing(16)
        lay.addWidget(_h1("스캔 진행 중"))
        self.scan_sub = QLabel("준비 중…")
        self.scan_sub.setStyleSheet("color:#565E6C; font-size:13px;")
        lay.addWidget(self.scan_sub)

        # 단계 인디케이터
        card = _card()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(22, 18, 22, 18)
        cl.setSpacing(14)
        stage_row = QHBoxLayout()
        stage_row.setSpacing(10)
        self._stage_labels = []
        for i, (ic, name) in enumerate([("📂", "파일 수집"), ("🔍", "내용 검사"), ("🧮", "검증·분석")]):
            s = QLabel(f"  {ic}  {name}")
            s.setObjectName("Card")
            s.setStyleSheet("background:#F7F8FA; border:1px solid #E7E9EE; border-radius:10px; padding:10px 12px; color:#8B92A0; font-weight:700;")
            self._stage_labels.append(s)
            stage_row.addWidget(s, 1)
        cl.addLayout(stage_row)
        pr = QHBoxLayout()
        pr.addWidget(QLabel("진행률"))
        pr.addStretch()
        self.pct_label = QLabel("0%")
        self.pct_label.setStyleSheet("font-size:26px; font-weight:800; color:#B0123F;")
        pr.addWidget(self.pct_label)
        cl.addLayout(pr)
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(14)
        cl.addWidget(self.progress_bar)
        self.progress_path = QLabel("준비 중...")
        self.progress_path.setStyleSheet("color:#8B92A0; font-family:'JetBrains Mono',monospace; font-size:11.5px;")
        cl.addWidget(self.progress_path)
        lay.addWidget(card)

        # 실시간 검출 버킷
        bgrid = QHBoxLayout()
        bgrid.setSpacing(12)
        self._bucket_labels = {}
        for key, color in [("주민등록번호", "#E11D2A"), ("신용카드번호", "#E11D2A"),
                           ("API키/DB", "#E08600"), ("전화·이메일", "#2563EB")]:
            bc = _card()
            bcl = QVBoxLayout(bc)
            bcl.setContentsMargins(16, 12, 16, 12)
            t = QLabel(key)
            t.setStyleSheet("color:#565E6C; font-size:12px; font-weight:600;")
            bcl.addWidget(t)
            v = QLabel("0")
            v.setStyleSheet(f"font-size:26px; font-weight:800; color:#8B92A0;")
            v.setProperty("color", color)
            self._bucket_labels[key] = v
            bcl.addWidget(v)
            bgrid.addWidget(bc, 1)
        lay.addLayout(bgrid)

        self.ocr_note = QLabel("🖼  이미지 분석 중 — 시간이 조금 걸릴 수 있어요")
        self.ocr_note.setAlignment(Qt.AlignCenter)
        self.ocr_note.setStyleSheet("color:#E08600; font-size:12.5px; font-weight:600;")
        self.ocr_note.setVisible(False)
        lay.addWidget(self.ocr_note)

        lay.addStretch()
        cancel = QPushButton("⏹  중지하고 결과 보기")
        cancel.setObjectName("Ghost")
        cancel.clicked.connect(self._cancel_scan)
        lay.addWidget(cancel, alignment=Qt.AlignCenter)
        return w

    # -------------------------------------------------------- 결과(3분할)
    def _build_results(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(36, 24, 36, 24)
        lay.setSpacing(14)

        head = QHBoxLayout()
        back = QPushButton("‹ 대시보드")
        back.setObjectName("Ghost")
        back.clicked.connect(lambda: (self._select_nav("dashboard"),
                                      self.stack.setCurrentWidget(self.dashboard)))
        head.addWidget(back)
        head.addStretch()
        self.report_btn = QPushButton("✓  점검 완료 · 리포트")
        self.report_btn.setObjectName("Primary")
        self.report_btn.clicked.connect(self.save_report)
        head.addWidget(self.report_btn)
        lay.addLayout(head)

        self.result_title = QLabel("점검 결과")
        self.result_title.setStyleSheet("font-size:22px; font-weight:800;")
        lay.addWidget(self.result_title)
        self.result_sub = QLabel("미리보기는 항상 마스킹된 형태로만 표시됩니다.")
        self.result_sub.setStyleSheet("color:#565E6C; font-size:12.5px;")
        lay.addWidget(self.result_sub)

        self.unread_banner = QLabel()
        self.unread_banner.setWordWrap(True)
        self.unread_banner.setStyleSheet(
            "background:#FEF3E0; border:1px solid #F6DDAE; border-radius:10px;"
            " color:#9A6B12; padding:10px 12px;")
        self.unread_banner.setVisible(False)
        lay.addWidget(self.unread_banner)

        body = QHBoxLayout()
        body.setSpacing(14)

        # 좌측 위험도 필터
        filt = _card()
        filt.setFixedWidth(180)
        fl = QVBoxLayout(filt)
        fl.setContentsMargins(16, 16, 16, 16)
        fl.setSpacing(8)
        fl.addWidget(self._mini_label("위험도"))
        self._sev_buttons = {}
        for key in ["전체", "높음", "중간", "낮음"]:
            b = QPushButton(key)
            b.setObjectName("Ghost")
            b.setCheckable(True)
            b.clicked.connect(lambda _=False, k=key: self._set_sev_filter(k))
            self._sev_buttons[key] = b
            fl.addWidget(b)
        self._sev_buttons["전체"].setChecked(True)
        fl.addWidget(self._mini_label("검색"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("파일·유형 검색")
        self.search_box.textChanged.connect(self._apply_filter)
        fl.addWidget(self.search_box)
        fl.addStretch()
        body.addWidget(filt)

        # 중앙 표
        center = QVBoxLayout()
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["위험도", "파일 / 위치", "검출 항목", "검출값(마스킹)"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self._update_preview)
        center.addWidget(self.table)
        bar = QHBoxLayout()
        for label, slot, obj in [("선택 마스킹", self._action_mask, "Ghost"),
                                 ("선택 격리", self._action_quarantine, "Ghost"),
                                 ("이건 오탐이에요", self._mark_false_positive, "Ghost"),
                                 ("완전삭제", self._action_delete, "Danger")]:
            b = QPushButton(label)
            b.setObjectName(obj)
            b.clicked.connect(slot)
            bar.addWidget(b)
        bar.addStretch()
        center.addLayout(bar)
        body.addLayout(center, 1)

        # 우측 미리보기
        self.preview = _card()
        self.preview.setFixedWidth(300)
        pv = QVBoxLayout(self.preview)
        pv.setContentsMargins(18, 18, 18, 18)
        pv.setSpacing(10)
        pv.addWidget(self._mini_label("🔎  마스킹 미리보기"))
        self.pv_file = QLabel("항목을 선택하세요")
        self.pv_file.setStyleSheet("font-weight:700; font-size:13.5px;")
        self.pv_file.setWordWrap(True)
        pv.addWidget(self.pv_file)
        self.pv_path = QLabel("")
        self.pv_path.setStyleSheet("color:#8B92A0; font-size:11.5px;")
        self.pv_path.setWordWrap(True)
        pv.addWidget(self.pv_path)
        self.pv_type = QLabel("")
        pv.addWidget(self.pv_type)
        self.pv_value = QLabel("")
        self.pv_value.setAlignment(Qt.AlignCenter)
        self.pv_value.setStyleSheet(
            "font-family:'JetBrains Mono','D2Coding',monospace; font-size:18px;"
            " background:#F7F8FA; border:1px solid #E7E9EE; border-radius:10px; padding:14px;")
        pv.addWidget(self.pv_value)
        ctxlbl = QLabel("검출 위치 (마스킹됨)")
        ctxlbl.setStyleSheet("color:#8B92A0; font-size:11.5px;")
        pv.addWidget(ctxlbl)
        self.pv_ctx = QLabel("")
        self.pv_ctx.setWordWrap(True)
        self.pv_ctx.setStyleSheet(
            "font-family:'JetBrains Mono',monospace; font-size:11.5px; color:#CBD3E1;"
            " background:#1B1E25; border-radius:10px; padding:12px;")
        pv.addWidget(self.pv_ctx)
        pv.addStretch()
        body.addWidget(self.preview)

        lay.addLayout(body, 1)
        return w

    def _mini_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size:12px; font-weight:700; color:#565E6C;")
        return lbl

    def _set_sev_filter(self, key: str):
        for k, b in self._sev_buttons.items():
            b.setChecked(k == key)
        self._apply_filter()

    # -------------------------------------------------------- 격리함
    def _build_quarantine(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(36, 28, 36, 28)
        lay.setSpacing(14)
        lay.addWidget(_h1("격리함"))
        d = QLabel("암호화되어 보관 중인 파일입니다. 선택해 원래 위치로 복원할 수 있습니다.")
        d.setStyleSheet("color:#565E6C;")
        lay.addWidget(d)
        self.q_table = QTableWidget(0, 3)
        self.q_table.setHorizontalHeaderLabels(["원본 경로", "격리 일시", "ID"])
        self.q_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.q_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.q_table.verticalHeader().setVisible(False)
        lay.addWidget(self.q_table)
        bar = QHBoxLayout()
        bar.addStretch()
        restore = QPushButton("↩  원래 위치로 복원")
        restore.setObjectName("Primary")
        restore.clicked.connect(self._restore_selected)
        bar.addWidget(restore)
        lay.addLayout(bar)
        return w

    def _refresh_quarantine(self):
        from . import actions
        self.q_table.setRowCount(0)
        qdir = actions.QUARANTINE_DIR
        if not qdir.exists():
            return
        for mf in sorted(qdir.glob("*.meta.json")):
            try:
                meta = json.loads(mf.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            r = self.q_table.rowCount()
            self.q_table.insertRow(r)
            self.q_table.setItem(r, 0, QTableWidgetItem(meta.get("original_path", "")))
            self.q_table.setItem(r, 1, QTableWidgetItem(meta.get("quarantined_at", "")))
            self.q_table.setItem(r, 2, QTableWidgetItem(meta.get("id", "")))

    def _restore_selected(self):
        rows = {i.row() for i in self.q_table.selectedIndexes()}
        if not rows:
            QMessageBox.information(self, "SoliGuard", "복원할 항목을 선택하세요.")
            return
        from .actions import restore_file
        ok = 0
        for r in rows:
            it = self.q_table.item(r, 2)
            if it and restore_file(it.text()).status == "success":
                ok += 1
        QMessageBox.information(self, "복원 완료", f"{ok}개 파일을 원래 위치로 복원했습니다.")
        self._refresh_quarantine()

    # -------------------------------------------------------- 점검 이력
    def _build_history(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(36, 28, 36, 28)
        lay.setSpacing(14)
        lay.addWidget(_h1("점검 이력"))
        d = QLabel("모든 점검·조치 내역입니다. 발주처 보안 감사·컴플라이언스 증빙으로 활용됩니다.")
        d.setStyleSheet("color:#565E6C;")
        lay.addWidget(d)
        self.h_table = QTableWidget(0, 4)
        self.h_table.setHorizontalHeaderLabels(["시각", "작업", "대상", "결과"])
        self.h_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.h_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.h_table.verticalHeader().setVisible(False)
        lay.addWidget(self.h_table)
        return w

    def _refresh_history(self):
        self.h_table.setRowCount(0)
        for e in reversed(_read_audit_tail(500)):
            r = self.h_table.rowCount()
            self.h_table.insertRow(r)
            self.h_table.setItem(r, 0, QTableWidgetItem(e.get("ts", "")))
            self.h_table.setItem(r, 1, QTableWidgetItem(
                _ACTION_KO.get(e.get("action", ""), e.get("action", ""))))
            self.h_table.setItem(r, 2, QTableWidgetItem(e.get("path", "")))
            self.h_table.setItem(r, 3, QTableWidgetItem(e.get("result", "")))

    # -------------------------------------------------------- 설정
    def _build_settings(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(36, 28, 36, 28)
        lay.setSpacing(16)
        lay.addWidget(_h1("설정"))

        gen = _card()
        gl = QVBoxLayout(gen)
        gl.setContentsMargins(22, 18, 22, 18)
        gl.setSpacing(10)
        gl.addWidget(self._mini_label("일반"))
        self.ocr_check = QCheckBox("이미지 속 신분증·계약서도 검사 (로컬 OCR)")
        self.ocr_check.setChecked(getattr(self.cfg, "ocr_mode", "local") != "off")
        gl.addWidget(self.ocr_check)
        fr = QHBoxLayout()
        fr.addWidget(QLabel("자동 점검 주기"))
        self.freq_box = QComboBox()
        self.freq_box.addItems(_FREQ_ITEMS)
        fr.addWidget(self.freq_box)
        fr.addStretch()
        gl.addLayout(fr)
        gl.addWidget(QLabel("직무 프로파일은 좌측 하단 칩에서 복수 선택할 수 있습니다."))
        self.font_info_label = QLabel("현재 글꼴: 확인 중…")
        self.font_info_label.setStyleSheet("color:#8B92A0; font-size:12px;")
        gl.addWidget(self.font_info_label)
        lay.addWidget(gen)

        try:
            from .ui.settings_figma import FigmaOptInSection
            self.figma_section = FigmaOptInSection()
            self.figma_section.scan_requested.connect(self.run_figma_scan)
            lay.addWidget(self.figma_section)
        except Exception:
            self.figma_section = None

        bar = QHBoxLayout()
        bar.addStretch()
        save = QPushButton("설정 저장")
        save.setObjectName("Primary")
        save.clicked.connect(self._save_settings)
        bar.addWidget(save)
        lay.addLayout(bar)
        lay.addStretch()
        return w

    def _save_settings(self):
        try:
            from .config import AppConfig, ScheduleConfig
            cfg = self.cfg or AppConfig.load()
            cfg.profiles = list(self.profiles)
            cfg.profile = self.profiles[0] if self.profiles else "개발자"
            cfg.ocr_mode = "local" if self.ocr_check.isChecked() else "off"
            enabled = self.freq_box.currentText() != "사용 안 함"
            freq = {"매일": "daily", "매주(월요일)": "weekly",
                    "매월(1일)": "monthly"}.get(self.freq_box.currentText(), "weekly")
            cfg.schedule = ScheduleConfig(enabled=enabled, frequency=freq)
            cfg.save()
            self.cfg = cfg
            QMessageBox.information(self, "설정", "설정을 저장했습니다.")
        except Exception as e:
            QMessageBox.warning(self, "설정 저장 실패", str(e))

    def _style_sev_label(self, lbl, sev):
        if sev is None:
            lbl.setStyleSheet("background:#F1F2F4; color:#8B92A0; border:1px solid #E7E9EE;"
                              "border-radius:10px; padding:2px 9px; font-weight:700; font-size:11px;")
            return
        color, bg, line = SEV_CHIP.get(sev, ("#8B92A0", "#F1F2F4", "#E7E9EE"))
        lbl.setText("● " + sev)
        lbl.setStyleSheet(f"background:{bg}; color:{color}; border:1px solid {line};"
                          "border-radius:10px; padding:2px 9px; font-weight:700; font-size:11px;")

    # -------------------------------------------------------- 스캔 설정
    def _build_scanconfig(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(32, 24, 32, 24)
        lay.setSpacing(14)
        back = QPushButton("‹ 대시보드")
        back.setObjectName("Ghost")
        back.setMaximumWidth(120)
        back.clicked.connect(lambda: (self._select_nav("dashboard"),
                                      self.stack.setCurrentWidget(self.dashboard)))
        lay.addWidget(back)
        lay.addWidget(_h1("스캔 설정"))
        self.sc_sub = QLabel("")
        self.sc_sub.setStyleSheet("color:#565E6C; font-size:13px;")
        lay.addWidget(self.sc_sub)

        cols = QHBoxLayout()
        cols.setSpacing(18)
        # 폴더
        fcard = _card()
        fl = QVBoxLayout(fcard)
        fl.setContentsMargins(20, 16, 20, 16)
        fl.setSpacing(8)
        fh = QHBoxLayout()
        ft = QLabel("스캔 대상 폴더")
        ft.setStyleSheet("font-size:15px; font-weight:800;")
        fh.addWidget(ft)
        fh.addStretch()
        addf = QPushButton("＋ 폴더 추가")
        addf.setObjectName("Ghost")
        addf.clicked.connect(self._add_scan_folder)
        fh.addWidget(addf)
        fl.addLayout(fh)
        self.sc_folder_box = QVBoxLayout()
        self.sc_folder_box.setSpacing(8)
        fl.addLayout(self.sc_folder_box)
        fl.addStretch()
        cols.addWidget(fcard, 1)
        # 검출 항목(직무 기반, 표시용)
        kcard = _card()
        kl = QVBoxLayout(kcard)
        kl.setContentsMargins(20, 16, 20, 16)
        kt = QLabel("검출할 항목")
        kt.setStyleSheet("font-size:15px; font-weight:800;")
        kl.addWidget(kt)
        self.sc_kinds = QLabel("")
        self.sc_kinds.setWordWrap(True)
        self.sc_kinds.setStyleSheet("color:#14161C; font-size:13px; line-height:1.7;")
        kl.addWidget(self.sc_kinds)
        kl.addStretch()
        cols.addWidget(kcard, 1)
        lay.addLayout(cols, 1)

        foot = QHBoxLayout()
        trust = QLabel("🔒 스캔은 이 PC 안에서만 수행되며, 검출된 데이터는 외부로 전송되지 않습니다.")
        trust.setStyleSheet("color:#8B92A0; font-size:12px;")
        foot.addWidget(trust)
        foot.addStretch()
        startb = QPushButton("🔍  스캔 시작")
        startb.setObjectName("Primary")
        startb.setMinimumHeight(44)
        startb.clicked.connect(self._begin_scan)
        foot.addWidget(startb)
        lay.addLayout(foot)
        return w

    def start_scan(self, *_):
        """호환용(트레이 메뉴 등): 스캔 설정 화면으로 진입."""
        self._go_scanconfig("full")

    def _go_scanconfig(self, scope: str):
        self._scan_scope = scope
        self._closing_mode = (scope == "closing")
        meta = {"full": "전체 스캔 — 지정한 폴더를 빠짐없이 검사합니다",
                "quick": "빠른 점검 — 위험 폴더만 빠르게 훑습니다",
                "closing": "프로젝트 클로징 점검 — 프로젝트 폴더의 잔여 발주처 데이터를 일괄 점검합니다"}[scope]
        self.sc_sub.setText(f"직무 “{', '.join(self.profiles)}” 기준 기본값입니다. · {meta}")
        # 추천 폴더 구성
        from .profiles import PROFILE_EXTENSIONS, PROFILE_FOLDERS
        names, seen = [], set()
        for role in self.profiles:
            for n in PROFILE_FOLDERS.get(role, []):
                if n not in seen:
                    seen.add(n); names.append(n)
        home = Path.home()
        self._sc_folders = []
        while self.sc_folder_box.count():
            it = self.sc_folder_box.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        for idx, n in enumerate(names):
            p = home / n
            on = p.exists() and (scope != "quick" or idx < 2)
            self._add_folder_row(str(p), on)
        # 검출 항목(직무 합집합 확장자)
        exts = set()
        for role in self.profiles:
            exts |= PROFILE_EXTENSIONS.get(role, set())
        kinds = ["주민등록번호", "신용카드", "전화·이메일", "계좌번호", "사업자번호"]
        if "개발자" in self.profiles:
            kinds.append("DB·API키(엔트로피 검증)")
        if any(self.cfg and getattr(self.cfg, "ocr_mode", "local") != "off" for _ in [0]):
            kinds.append("이미지 속 정보(OCR)")
        self.sc_kinds.setText("✓ " + "\n✓ ".join(kinds) +
                              f"\n\n파일 형식: {', '.join(sorted(e.lstrip('.') for e in exts))}")
        self._select_nav("dashboard")
        self.stack.setCurrentWidget(self.scanconfig)

    def _add_folder_row(self, path: str, on: bool):
        b = QPushButton(f"  📁  {path}")
        b.setObjectName("ChkCardG")
        b.setCheckable(True)
        b.setChecked(on)
        b.setStyleSheet(
            "QPushButton{background:#fff;border:1px solid #E7E9EE;border-radius:10px;"
            "padding:10px 12px;text-align:left;color:#14161C;font-family:'JetBrains Mono',monospace;font-size:12px;}"
            "QPushButton:checked{border:1px solid #F6D2DE;background:#FCEFF3;}")
        self.sc_folder_box.addWidget(b)
        self._sc_folders.append((b, path))

    def _add_scan_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "폴더 추가")
        if folder:
            self._add_folder_row(folder, True)

    def _begin_scan(self):
        folders = [p for b, p in self._sc_folders if b.isChecked()]
        if not folders:
            QMessageBox.information(self, "SoliGuard", "스캔할 폴더를 한 곳 이상 선택하세요.")
            return
        self.stack.setCurrentWidget(self.scanning)
        self.progress_bar.setValue(0)
        self.pct_label.setText("0%")
        for v in self._bucket_labels.values():
            v.setText("0"); v.setStyleSheet("font-size:26px; font-weight:800; color:#8B92A0;")
        ocr_enabled = self.ocr_check.isChecked() if hasattr(self, "ocr_check") else True
        wl = list(getattr(self.cfg, "whitelist", []) or [])
        self.worker = ScanWorker([Path(f) for f in folders], list(self.profiles), ocr_enabled, wl)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished_scan.connect(self._on_finished)
        self.worker.start()

    def _cancel_scan(self):
        if self.worker:
            self.worker.stop()

    def _on_progress(self, done, total, path, buckets):
        pct = int(done / total * 100) if total else 100
        self.progress_bar.setMaximum(total or 1)
        self.progress_bar.setValue(done)
        self.pct_label.setText(f"{pct}%")
        self.progress_path.setText(f"검사 중  {path}")
        self.scan_sub.setText(f"검사 {done:,} / {total:,}개 파일")
        # 단계 강조
        stage = 0 if pct < 10 else (1 if pct < 86 else 2)
        for i, s in enumerate(self._stage_labels):
            if i < stage:
                s.setStyleSheet("background:#fff;border:1px solid #E7E9EE;border-radius:10px;padding:10px 12px;color:#15A34A;font-weight:700;")
            elif i == stage:
                s.setStyleSheet("background:#FCEFF3;border:1px solid #F6D2DE;border-radius:10px;padding:10px 12px;color:#B0123F;font-weight:700;")
            else:
                s.setStyleSheet("background:#F7F8FA;border:1px solid #E7E9EE;border-radius:10px;padding:10px 12px;color:#8B92A0;font-weight:700;")
        for key, v in self._bucket_labels.items():
            n = buckets.get(key, 0)
            color = v.property("color") if n else "#8B92A0"
            v.setText(str(n))
            v.setStyleSheet(f"font-size:26px; font-weight:800; color:{color};")
        self.ocr_note.setVisible(self.ocr_check.isChecked() if hasattr(self, "ocr_check") else False)

    def _on_finished(self, summary):
        self.file_results = summary.file_results
        skipped = summary.skipped
        total = summary.total_findings
        grade = summary.risk_grade
        # 위험도별 카운트
        bysev = {"높음": 0, "중간": 0, "낮음": 0}
        for r in summary.file_results:
            for f in r.findings:
                bysev[f.severity.value] = bysev.get(f.severity.value, 0) + 1
        # 대시보드 갱신
        self.donut.set_data(bysev, grade)
        sev_for_chip = {"위험": "높음", "주의": "중간", "안전": "낮음"}.get(grade, "낮음")
        if total == 0 and skipped > 0:
            self.grade_chip_label.setText("확인 필요")
            self._style_sev_label(self.grade_chip_label, "중간")
            self.grade_label.setText(
                f"위험은 발견되지 않았지만 {skipped}개 파일을 검사하지 못했습니다(파서/OCR 미설치 등).")
        else:
            self._style_sev_label(self.grade_chip_label, sev_for_chip)
            if total:
                self.grade_label.setText(
                    f"주의가 필요한 항목 {total}건을 발견했어요. "
                    + {"위험": "즉시 조치가 필요해요.", "주의": "주의가 필요해요."}.get(grade, ""))
            else:
                self.grade_label.setText("점검한 파일에서 위험을 찾지 못했습니다. 안전합니다.")
        self.dash_sub.setText(f"마지막 점검 방금 · {summary.scanned:,}개 파일 검사 · 검사불가 {skipped}")
        self.stat_role._value_label.setText(", ".join(self.profiles))
        try:
            from . import actions
            qn = len(list(actions.QUARANTINE_DIR.glob("*.meta.json"))) if actions.QUARANTINE_DIR.exists() else 0
            self.stat_quar._value_label.setText(f"{qn}개")
        except Exception:
            pass

        self.result_title.setText(
            f"점검 결과 — 위험 {summary.total_findings}건 발견")
        self.result_sub.setText(
            f"미리보기는 항상 마스킹된 형태로만 표시됩니다 · 검사 {summary.scanned} / 검사불가 {skipped}")

        if skipped > 0:
            names = [r.path.name for r in summary.file_results if r.status == "검사불가"][:8]
            more = "" if skipped <= 8 else f" 외 {skipped - 8}건"
            self.unread_banner.setText(
                f"⚠  {skipped}개 파일을 검사하지 못했습니다(파서/OCR 미설치 또는 손상). "
                f"위험 여부를 확인하지 못했습니다.\n· " + ", ".join(names) + more)
            self.unread_banner.setVisible(True)
        else:
            self.unread_banner.setVisible(False)

        self._populate_table(summary.file_results)
        self._render_recent()

        if summary.total_findings == 0 and skipped == 0:
            QMessageBox.information(
                self, "점검 완료",
                f"🟢 안전합니다 — 점검한 {summary.scanned}개 파일에서 위험을 찾지 못했어요.")
            self.stack.setCurrentWidget(self.dashboard)
        else:
            self.stack.setCurrentWidget(self.results)
        self.scan_finished.emit(
            "warn" if (summary.total_findings == 0 and skipped > 0)
            else summary.risk_grade_key)

        if self._closing_mode:
            self._closing_mode = False
            if QMessageBox.question(
                self, "프로젝트 클로징 점검",
                "프로젝트 점검이 끝났습니다. 보안 증빙용 진단 리포트(PDF)를 발급할까요?"
            ) == QMessageBox.Yes:
                self.save_report()

    def _populate_table(self, results):
        self.table.setRowCount(0)
        self.row_index = []
        for r in results:
            for f in r.findings:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(f.severity.value))
                self.table.setCellWidget(row, 0, _sev_chip(f.severity.value))
                self.table.setItem(row, 1, QTableWidgetItem(str(r.path)))
                self.table.setItem(row, 2, QTableWidgetItem(f.info_type))
                self.table.setItem(row, 3, QTableWidgetItem(f.masked))
                self.row_index.append((Path(r.path), f))
        if hasattr(self, "_sev_buttons"):
            self._apply_filter()

    # -------------------------------------------------------- 필터/미리보기
    def _apply_filter(self, *_):
        sev = next((k for k, b in self._sev_buttons.items() if b.isChecked()), "전체")
        q = self.search_box.text().strip().lower()
        for row in range(self.table.rowCount()):
            sev_v = self.table.item(row, 0).text() if self.table.item(row, 0) else ""
            text = " ".join(
                self.table.item(row, c).text() if self.table.item(row, c) else ""
                for c in range(1, self.table.columnCount())).lower()
            show = (sev == "전체" or sev_v == sev) and (not q or q in text)
            self.table.setRowHidden(row, not show)

    def _update_preview(self):
        rows = {i.row() for i in self.table.selectedIndexes()}
        if not rows:
            return
        path, f = self.row_index[min(rows)]
        self.pv_file.setText(path.name)
        self.pv_path.setText(f"{path}  ·  line {f.line}")
        color, bg, line = SEV_CHIP.get(f.severity.value, ("#8B92A0", "#F1F2F4", "#E7E9EE"))
        self.pv_type.setText(
            f'{f.info_type}　<span style="color:{color};font-weight:700;">● {f.severity.value}</span>')
        self.pv_value.setText(f.masked)
        ctx = f.context or ""
        if f.raw and f.raw in ctx:
            ctx = ctx.replace(f.raw, f.masked)
        self.pv_ctx.setText(ctx or "(문맥 없음)")

    # -------------------------------------------------------- 조치
    def _selected_by_file(self):
        grouped = {}
        for idx in {i.row() for i in self.table.selectedIndexes()}:
            path, finding = self.row_index[idx]
            grouped.setdefault(path, []).append(finding)
        return grouped

    def _require(self, grouped):
        if not grouped:
            QMessageBox.information(self, "SoliGuard", "처리할 행을 선택하세요.")
            return False
        return True

    def _action_mask(self):
        g = self._selected_by_file()
        if not self._require(g):
            return
        from .actions import mask_in_text_file
        ok = sum(1 for p, fs in g.items() if mask_in_text_file(p, fs).status == "success")
        QMessageBox.information(self, "마스킹 완료", f"{ok}개 파일의 마스킹 사본을 생성했습니다.")
        self._render_recent()

    def _action_quarantine(self):
        g = self._selected_by_file()
        if not self._require(g):
            return
        from .actions import quarantine_file
        ok = sum(1 for p in g if quarantine_file(p).status == "success")
        QMessageBox.information(self, "격리 완료", f"{ok}개 파일을 암호화 격리함으로 옮겼습니다.")
        self._render_recent()

    def _action_delete(self):
        g = self._selected_by_file()
        if not self._require(g):
            return
        text, ok = QInputDialog.getText(
            self, "완전 삭제 확인",
            f"선택한 {len(g)}개 파일을 복구 불가능하게 삭제합니다.\n"
            "되돌릴 수 없습니다. 확인을 위해 '삭제'를 입력하세요:")
        if not ok or text.strip() != "삭제":
            return
        from .actions import secure_delete
        done = sum(1 for p in g if secure_delete(p, confirmed=True).status == "success")
        QMessageBox.information(self, "삭제 완료", f"{done}개 파일을 영구 삭제했습니다.")
        self._render_recent()

    def _mark_false_positive(self):
        rows = sorted({i.row() for i in self.table.selectedIndexes()})
        if not rows:
            QMessageBox.information(self, "SoliGuard", "오탐으로 표시할 행을 선택하세요.")
            return
        from .config import AppConfig
        cfg = self.cfg or AppConfig.load()
        wl = list(cfg.whitelist or [])
        added = 0
        for r in rows:
            _, f = self.row_index[r]
            if f.raw not in wl:
                wl.append(f.raw)
                added += 1
            self.table.setRowHidden(r, True)
        cfg.whitelist = wl
        cfg.save()
        self.cfg = cfg
        QMessageBox.information(self, "오탐 등록",
                                f"{added}건을 오탐(제외)으로 등록했습니다. 다음 점검부터 제외됩니다.")

    def save_report(self):
        if not self.file_results:
            QMessageBox.information(self, "SoliGuard", "먼저 점검을 실행하세요.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "리포트 저장", "soliguard_report.pdf", "PDF (*.pdf)")
        if not path:
            return
        try:
            generate_pdf_report(self.file_results, ", ".join(self.profiles), Path(path))
            QMessageBox.information(self, "리포트 저장", f"저장됨: {path}")
        except ReportError as e:
            QMessageBox.warning(self, "리포트 생성 실패", str(e))

    def run_figma_scan(self, url, token, consent):
        from .figma_scan import (
            FigmaApiError, FigmaConsentError, parse_file_key, scan_figma_file)
        try:
            key = parse_file_key(url)
            result = scan_figma_file(key, token, user_consented=consent)
        except FigmaConsentError as e:
            QMessageBox.warning(self, "동의 필요", str(e))
            return
        except (FigmaApiError, ValueError) as e:
            QMessageBox.critical(self, "Figma 검사 실패", str(e))
            return
        QMessageBox.information(
            self, "Figma 검사 완료",
            f"'{result.file_name}'에서 텍스트 {result.text_node_count}개 검사, "
            f"위험 {len(result.findings)}건 발견")

    def closeEvent(self, event):
        if self._tray_active:
            event.ignore()
            self.hide()
        else:
            event.accept()


def _read_audit_tail(n: int) -> list:
    try:
        from . import actions
        if not actions.AUDIT_LOG.exists():
            return []
        lines = actions.AUDIT_LOG.read_text(encoding="utf-8").strip().splitlines()
        out = []
        for line in lines[-n:]:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out
    except Exception:
        return []


def main() -> int:
    app = QApplication(sys.argv)
    fonts.load_fonts(app)
    app.setWindowIcon(icons.app_icon())
    app.setStyleSheet(build_qss("light"))
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
