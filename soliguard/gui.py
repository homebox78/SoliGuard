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


# ---------------------------------------------------------------- 스캔 워커
class ScanWorker(QThread):
    progress = Signal(int, int, str)
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
        summary = run_scan(
            self.folders, profiles=self.profiles, ocr_enabled=self.ocr_enabled,
            user_whitelist=self.user_whitelist,
            progress_cb=lambda i, t, p: self.progress.emit(i, t, p),
            should_stop=lambda: self._stop,
        )
        self.finished_scan.emit(summary)


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
        self.results = self._build_results()
        self.quarantine = self._build_quarantine()
        self.history = self._build_history()
        self.settings = self._build_settings()
        for wdg in (self.dashboard, self.scanning, self.results,
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
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(36, 30, 36, 30)
        lay.setSpacing(18)
        lay.addWidget(_h1("보안 대시보드"))

        card = _card()
        cl = QHBoxLayout(card)
        cl.setContentsMargins(26, 22, 26, 22)
        self.grade_dot = QLabel()
        self.grade_dot.setFixedSize(16, 16)
        self.grade_dot.setStyleSheet("background:#8B92A0; border-radius:8px;")
        cl.addWidget(self.grade_dot)
        self.grade_label = QLabel("내 PC 위험 등급: 아직 점검하지 않음")
        self.grade_label.setStyleSheet("font-size:19px; font-weight:800;")
        cl.addWidget(self.grade_label)
        cl.addStretch()
        self.last_scan_label = QLabel("마지막 점검: -")
        self.last_scan_label.setStyleSheet("color:#8B92A0;")
        cl.addWidget(self.last_scan_label)
        lay.addWidget(card)

        scan_btn = QPushButton("🔍   지금 점검하기")
        scan_btn.setObjectName("Primary")
        scan_btn.setMinimumHeight(60)
        scan_btn.setStyleSheet("font-size:16px;")
        scan_btn.setCursor(Qt.PointingHandCursor)
        scan_btn.clicked.connect(lambda: self.start_scan(False))
        lay.addWidget(scan_btn)

        closing = QPushButton("📁   프로젝트 클로징 점검 — 종료 프로젝트 폴더 일괄 점검·리포트")
        closing.setObjectName("Ghost")
        closing.setMinimumHeight(44)
        closing.setCursor(Qt.PointingHandCursor)
        closing.clicked.connect(lambda: self.start_scan(True))
        lay.addWidget(closing)

        recent = _card()
        rl = QVBoxLayout(recent)
        rl.setContentsMargins(22, 18, 22, 18)
        rt = QLabel("최근 활동")
        rt.setStyleSheet("font-size:14px; font-weight:700;")
        rl.addWidget(rt)
        self.recent_box = QVBoxLayout()
        rl.addLayout(self.recent_box)
        self._render_recent()
        lay.addWidget(recent, 1)
        return w

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
        lay.setContentsMargins(36, 30, 36, 30)
        lay.addWidget(_h1("스캔 진행 중"))
        lay.addStretch()
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        lay.addWidget(self.progress_bar)
        self.progress_path = QLabel("준비 중...")
        self.progress_path.setStyleSheet("color:#8B92A0;")
        lay.addWidget(self.progress_path)
        cancel = QPushButton("중지")
        cancel.setObjectName("Ghost")
        cancel.clicked.connect(self._cancel_scan)
        lay.addWidget(cancel, alignment=Qt.AlignRight)
        lay.addStretch()
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

    # -------------------------------------------------------- 스캔 동작
    def start_scan(self, closing: bool = False):
        title = "프로젝트 폴더 선택 (클로징 점검)" if closing else "스캔할 폴더 선택"
        folder = QFileDialog.getExistingDirectory(self, title)
        if not folder:
            return
        self._closing_mode = closing
        self._select_nav("dashboard")
        self.stack.setCurrentWidget(self.scanning)
        self.progress_bar.setValue(0)
        ocr_enabled = self.ocr_check.isChecked() if hasattr(self, "ocr_check") else True
        wl = list(getattr(self.cfg, "whitelist", []) or [])
        self.worker = ScanWorker([Path(folder)], list(self.profiles), ocr_enabled, wl)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished_scan.connect(self._on_finished)
        self.worker.start()

    def _cancel_scan(self):
        if self.worker:
            self.worker.stop()

    def _on_progress(self, done, total, path):
        self.progress_bar.setMaximum(total or 1)
        self.progress_bar.setValue(done)
        self.progress_path.setText(f"검사 중: {path}")

    def _on_finished(self, summary):
        self.file_results = summary.file_results
        skipped = summary.skipped
        disp = GRADE_DISPLAY.get(summary.risk_grade, {})
        color = disp.get("color", "#8B92A0")
        if summary.total_findings == 0 and skipped > 0:
            color = SEMANTIC["warn"]
            self.grade_label.setText(f"내 PC 위험 등급: 🟡 확인 필요 (미검사 {skipped}건)")
        else:
            self.grade_label.setText(f"내 PC 위험 등급: {disp.get('icon','')} {summary.risk_grade}")
        self.grade_dot.setStyleSheet(f"background:{color}; border-radius:8px;")
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
