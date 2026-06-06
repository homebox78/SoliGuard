"""PySide6 GUI - 상용 수준 데스크톱 앱.

좌측 사이드바 내비게이션(대시보드/격리함/점검 이력/설정) + 우측 콘텐츠(QStackedWidget).
스캔은 별도 스레드(ScanWorker)에서 돌려 UI가 멈추지 않게 한다.

실행:  py -m soliguard.gui   (또는 py -m soliguard.app — 트레이 상주 포함)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QComboBox, QFileDialog, QFrame,
    QGraphicsDropShadowEffect, QHBoxLayout, QHeaderView, QInputDialog, QLabel,
    QMainWindow, QMessageBox, QProgressBar, QPushButton, QStackedWidget,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from . import __version__ as _VERSION
from . import fonts, icons

from .engine import PROFILE_ROLE, run_scan
from .report import ReportError, generate_pdf_report
from .theme import GRADE_DISPLAY, SEMANTIC, build_qss

_FREQ_ITEMS = ["사용 안 함", "매일", "매주(월요일)", "매월(1일)"]


class ScanWorker(QThread):
    """스캔을 백그라운드에서 실행. 진행률/완료를 시그널로 전달."""

    progress = Signal(int, int, str)   # done, total, current_path
    finished_scan = Signal(object)     # engine.ScanSummary

    def __init__(self, folders, role, ocr_enabled):
        super().__init__()
        self.folders = folders
        self.role = role
        self.ocr_enabled = ocr_enabled
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        summary = run_scan(
            self.folders, role=self.role, ocr_enabled=self.ocr_enabled,
            progress_cb=lambda i, t, p: self.progress.emit(i, t, p),
            should_stop=lambda: self._stop,
        )
        self.finished_scan.emit(summary)


def _h1(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet("font-size:22px; font-weight:700;")
    return lbl


def _card() -> QFrame:
    f = QFrame()
    f.setObjectName("Card")
    eff = QGraphicsDropShadowEffect(f)
    eff.setBlurRadius(24)
    eff.setOffset(0, 4)
    eff.setColor(QColor(80, 10, 30, 28))
    f.setGraphicsEffect(eff)
    return f


class MainWindow(QMainWindow):
    scan_finished = Signal(str)  # risk_grade_key

    def __init__(self, cfg=None):
        super().__init__()
        self.setWindowTitle("SoliGuard")
        self.setWindowIcon(icons.app_icon())
        self.resize(1280, 820)
        self.cfg = cfg
        self.profile = getattr(cfg, "profile", None) or "개발자"
        self.theme = getattr(cfg, "theme", None) or "light"
        self.worker: ScanWorker | None = None
        self.file_results: list = []
        self.row_index: list[tuple[Path, object]] = []
        self._tray_active = False

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
        for w in (self.dashboard, self.scanning, self.results,
                  self.quarantine, self.history, self.settings):
            self.stack.addWidget(w)
        row.addWidget(self.stack, 1)
        self.setCentralWidget(root)
        self.stack.setCurrentWidget(self.dashboard)

    # ------------------------------------------------------------------ 사이드바
    def _build_sidebar(self) -> QWidget:
        side = QWidget()
        side.setObjectName("Sidebar")
        side.setFixedWidth(248)
        lay = QVBoxLayout(side)
        lay.setContentsMargins(0, 20, 0, 16)
        lay.setSpacing(2)

        # 로고 락업 (실제 solideo 로고 우선, 없으면 텍스트)
        logo = QLabel()
        logo_pix = icons.logo_pixmap(24, white=True)
        if logo_pix is not None:
            logo.setPixmap(logo_pix)
            logo.setStyleSheet("padding:6px 24px 0 24px;")
        else:
            logo.setText(
                '<span style="color:white;font-weight:800;">solideo</span>'
                '<span style="color:#F472A6;font-weight:800;">S.</span>')
            logo.setStyleSheet("font-size:20px; padding:6px 24px 0 24px;")
        lay.addWidget(logo)
        prod = QLabel("SoliGuard")
        prod.setStyleSheet("font-size:15px; font-weight:700; padding:0 24px;")
        lay.addWidget(prod)
        sub = QLabel(f"개인정보 점검 · v{_VERSION}")
        sub.setStyleSheet("font-size:11px; color:rgba(255,255,255,0.55); padding:0 24px 14px 24px;")
        lay.addWidget(sub)

        # 내비게이션
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self._nav_buttons = {}
        for key, label in [("dashboard", "📊  대시보드"), ("quarantine", "🔒  격리함"),
                           ("history", "🕘  점검 이력"), ("settings", "⚙  설정")]:
            b = QPushButton(label)
            b.setCheckable(True)
            b.clicked.connect(lambda _=False, k=key: self._navigate(k))
            self.nav_group.addButton(b)
            self._nav_buttons[key] = b
            lay.addWidget(b)
        self._nav_buttons["dashboard"].setChecked(True)

        lay.addStretch()

        # 직무 선택(하단)
        role_lbl = QLabel("직무")
        role_lbl.setStyleSheet("font-size:12px; color:rgba(255,255,255,0.65); padding:0 24px;")
        lay.addWidget(role_lbl)
        wrap = QWidget()
        wl = QHBoxLayout(wrap)
        wl.setContentsMargins(24, 4, 24, 4)
        self.profile_box = QComboBox()
        self.profile_box.addItems(list(PROFILE_ROLE.keys()))
        if self.profile in PROFILE_ROLE:
            self.profile_box.setCurrentText(self.profile)
        self.profile_box.currentTextChanged.connect(self._on_profile_changed)
        wl.addWidget(self.profile_box)
        lay.addWidget(wrap)

        trust = QLabel("로컬 전용 · 외부 전송 없음")
        trust.setStyleSheet("font-size:11px; color:rgba(255,255,255,0.55); padding:10px 24px 0 24px;")
        lay.addWidget(trust)
        return side

    def _navigate(self, key: str):
        if key == "dashboard":
            self.stack.setCurrentWidget(self.dashboard)
        elif key == "quarantine":
            self._refresh_quarantine()
            self.stack.setCurrentWidget(self.quarantine)
        elif key == "history":
            self._refresh_history()
            self.stack.setCurrentWidget(self.history)
        elif key == "settings":
            self.stack.setCurrentWidget(self.settings)

    def _select_nav(self, key: str):
        self._nav_buttons[key].setChecked(True)

    # ------------------------------------------------------------------ 대시보드
    def _build_dashboard(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(36, 32, 36, 32)
        lay.setSpacing(18)
        lay.addWidget(_h1("대시보드"))

        # 위험 등급 카드
        card = _card()
        cl = QHBoxLayout(card)
        cl.setContentsMargins(28, 24, 28, 24)
        self.grade_dot = QLabel()
        self.grade_dot.setFixedSize(18, 18)
        self.grade_dot.setStyleSheet("background:#94A3B8; border-radius:9px;")
        cl.addWidget(self.grade_dot)
        self.grade_label = QLabel("내 PC 위험 등급: 아직 점검하지 않음")
        self.grade_label.setStyleSheet("font-size:20px; font-weight:700;")
        cl.addWidget(self.grade_label)
        cl.addStretch()
        self.last_scan_label = QLabel("마지막 점검: -")
        self.last_scan_label.setStyleSheet("color:#7A6A70;")
        cl.addWidget(self.last_scan_label)
        lay.addWidget(card)

        # 큰 점검 버튼
        scan_btn = QPushButton("🔍   지금 점검하기")
        scan_btn.setObjectName("Primary")
        scan_btn.setMinimumHeight(66)
        scan_btn.setStyleSheet("font-size:18px;")
        scan_btn.setCursor(Qt.PointingHandCursor)
        scan_btn.clicked.connect(self.start_scan)
        lay.addWidget(scan_btn)
        hint = QLabel("🔒  모든 데이터는 이 PC 안에서만 처리되며 외부로 전송되지 않습니다.")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color:#7A6A70; padding:2px;")
        lay.addWidget(hint)

        # 최근 활동
        recent = _card()
        rl = QVBoxLayout(recent)
        rl.setContentsMargins(24, 18, 24, 18)
        rt = QLabel("최근 활동")
        rt.setStyleSheet("font-size:15px; font-weight:600;")
        rl.addWidget(rt)
        self.recent_box = QVBoxLayout()
        rl.addLayout(self.recent_box)
        self._render_recent()
        lay.addWidget(recent, 1)
        return w

    def _render_recent(self):
        # 기존 항목 제거
        while self.recent_box.count():
            item = self.recent_box.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        entries = _read_audit_tail(5)
        if not entries:
            empty = QLabel("아직 점검 이력이 없습니다. ‘지금 점검하기’로 첫 점검을 시작하세요.")
            empty.setStyleSheet("color:#7A6A70; padding:8px 0;")
            self.recent_box.addWidget(empty)
            return
        for e in entries:
            row = QLabel(f"· {e.get('ts','')}  {_ACTION_KO.get(e.get('action',''), e.get('action',''))}  "
                        f"{Path(e.get('path','')).name}  [{e.get('result','')}]")
            row.setStyleSheet("color:#3A2C30; padding:3px 0;")
            self.recent_box.addWidget(row)

    # ------------------------------------------------------------------ 스캔 진행
    def _build_scanning(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(36, 32, 36, 32)
        lay.addWidget(_h1("스캔 진행 중"))
        lay.addStretch()
        self.progress_bar = QProgressBar()
        lay.addWidget(self.progress_bar)
        self.progress_path = QLabel("준비 중...")
        self.progress_path.setStyleSheet("color:#7A6A70;")
        lay.addWidget(self.progress_path)
        cancel = QPushButton("중지")
        cancel.setObjectName("Ghost")
        cancel.clicked.connect(self._cancel_scan)
        lay.addWidget(cancel, alignment=Qt.AlignRight)
        lay.addStretch()
        return w

    # ------------------------------------------------------------------ 결과
    def _build_results(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(36, 28, 36, 28)
        lay.setSpacing(14)
        head = QHBoxLayout()
        self.result_title = _h1("점검 결과")
        head.addWidget(self.result_title)
        head.addStretch()
        back = QPushButton("← 대시보드")
        back.setObjectName("Ghost")
        back.clicked.connect(lambda: (self._select_nav("dashboard"),
                                      self.stack.setCurrentWidget(self.dashboard)))
        head.addWidget(back)
        lay.addLayout(head)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["위험도", "파일", "검출 항목", "검출값(마스킹)"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        lay.addWidget(self.table)

        bar = QHBoxLayout()
        for label, slot, ghost in [("선택 마스킹", self._action_mask, True),
                                   ("선택 격리", self._action_quarantine, True),
                                   ("선택 완전삭제", self._action_delete, False)]:
            b = QPushButton(label)
            b.setObjectName("Ghost" if ghost else "Danger")
            b.clicked.connect(slot)
            bar.addWidget(b)
        bar.addStretch()
        report_btn = QPushButton("📑  리포트 저장")
        report_btn.setObjectName("Primary")
        report_btn.clicked.connect(self.save_report)
        bar.addWidget(report_btn)
        lay.addLayout(bar)
        return w

    # ------------------------------------------------------------------ 격리함
    def _build_quarantine(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(36, 28, 36, 28)
        lay.setSpacing(14)
        lay.addWidget(_h1("격리함"))
        desc = QLabel("암호화되어 보관 중인 파일입니다. 선택해 원래 위치로 복원할 수 있습니다.")
        desc.setStyleSheet("color:#7A6A70;")
        lay.addWidget(desc)
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
        for meta_file in sorted(qdir.glob("*.meta.json")):
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
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
            qid_item = self.q_table.item(r, 2)
            if qid_item and restore_file(qid_item.text()).status == "success":
                ok += 1
        QMessageBox.information(self, "복원 완료", f"{ok}개 파일을 원래 위치로 복원했습니다.")
        self._refresh_quarantine()

    # ------------------------------------------------------------------ 점검 이력
    def _build_history(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(36, 28, 36, 28)
        lay.setSpacing(14)
        lay.addWidget(_h1("점검 이력 (감사 로그)"))
        desc = QLabel("모든 점검·조치 내역입니다. 발주처 보안 감사·컴플라이언스 증빙으로 활용됩니다.")
        desc.setStyleSheet("color:#7A6A70;")
        lay.addWidget(desc)
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

    # ------------------------------------------------------------------ 설정
    def _build_settings(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(36, 28, 36, 28)
        lay.setSpacing(16)
        lay.addWidget(_h1("설정"))

        gen = _card()
        gl = QVBoxLayout(gen)
        gl.setContentsMargins(22, 18, 22, 18)
        gl.addWidget(QLabel("일반"))
        self.ocr_check = QCheckBox("이미지 속 신분증·계약서도 검사 (로컬 OCR)")
        self.ocr_check.setChecked(getattr(self.cfg, "ocr_mode", "local") != "off")
        gl.addWidget(self.ocr_check)
        freq_row = QHBoxLayout()
        freq_row.addWidget(QLabel("자동 점검 주기"))
        self.freq_box = QComboBox()
        self.freq_box.addItems(_FREQ_ITEMS)
        freq_row.addWidget(self.freq_box)
        freq_row.addStretch()
        gl.addLayout(freq_row)
        lay.addWidget(gen)

        # Figma 옵트인 섹션
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
            cfg.profile = self.profile
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

    # ------------------------------------------------------------------ 동작
    def _on_profile_changed(self, text: str):
        self.profile = text

    def start_scan(self):
        folder = QFileDialog.getExistingDirectory(self, "스캔할 폴더 선택")
        if not folder:
            return
        self._select_nav("dashboard")
        self.stack.setCurrentWidget(self.scanning)
        self.progress_bar.setValue(0)
        ocr = getattr(self, "ocr_check", None)
        ocr_enabled = ocr.isChecked() if ocr else True
        self.worker = ScanWorker([Path(folder)], PROFILE_ROLE.get(self.profile), ocr_enabled)
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
        disp = GRADE_DISPLAY.get(summary.risk_grade, {})
        color = disp.get("color", "#94A3B8")
        self.grade_dot.setStyleSheet(f"background:{color}; border-radius:9px;")
        self.grade_label.setText(f"내 PC 위험 등급: {disp.get('icon','')} {summary.risk_grade}")
        self.result_title.setText(
            f"점검 결과 — 위험 {summary.total_findings}건 "
            f"(검사 {summary.scanned} / 검사불가 {summary.skipped})")
        self._populate_table(summary.file_results)
        self._render_recent()
        if summary.total_findings == 0:
            QMessageBox.information(
                self, "점검 완료",
                f"🟢 안전합니다 — 점검한 {summary.scanned}개 파일에서 위험을 찾지 못했어요.")
            self.stack.setCurrentWidget(self.dashboard)
        else:
            self.stack.setCurrentWidget(self.results)
        self.scan_finished.emit(summary.risk_grade_key)

    def _populate_table(self, results):
        self.table.setRowCount(0)
        self.row_index = []
        for r in results:
            for f in r.findings:
                row = self.table.rowCount()
                self.table.insertRow(row)
                sev = QTableWidgetItem(f.severity.value)
                self.table.setItem(row, 0, sev)
                self.table.setItem(row, 1, QTableWidgetItem(str(r.path)))
                self.table.setItem(row, 2, QTableWidgetItem(f.info_type))
                self.table.setItem(row, 3, QTableWidgetItem(f.masked))
                self.row_index.append((Path(r.path), f))

    def _selected_by_file(self):
        grouped: dict[Path, list] = {}
        for idx in {i.row() for i in self.table.selectedIndexes()}:
            path, finding = self.row_index[idx]
            grouped.setdefault(path, []).append(finding)
        return grouped

    def _action_mask(self):
        grouped = self._selected_by_file()
        if not self._require_selection(grouped):
            return
        from .actions import mask_in_text_file

        ok = sum(1 for p, fs in grouped.items()
                 if mask_in_text_file(p, fs).status == "success")
        QMessageBox.information(self, "마스킹 완료", f"{ok}개 파일의 마스킹 사본을 생성했습니다.")
        self._render_recent()

    def _action_quarantine(self):
        grouped = self._selected_by_file()
        if not self._require_selection(grouped):
            return
        from .actions import quarantine_file

        ok = sum(1 for p in grouped if quarantine_file(p).status == "success")
        QMessageBox.information(self, "격리 완료", f"{ok}개 파일을 암호화 격리함으로 옮겼습니다.")
        self._render_recent()

    def _action_delete(self):
        grouped = self._selected_by_file()
        if not self._require_selection(grouped):
            return
        text, ok = QInputDialog.getText(
            self, "완전 삭제 확인",
            f"선택한 {len(grouped)}개 파일을 복구 불가능하게 삭제합니다.\n"
            "되돌릴 수 없습니다. 확인을 위해 '삭제'를 입력하세요:")
        if not ok or text.strip() != "삭제":
            return
        from .actions import secure_delete

        done = sum(1 for p in grouped
                   if secure_delete(p, confirmed=True).status == "success")
        QMessageBox.information(self, "삭제 완료", f"{done}개 파일을 영구 삭제했습니다.")
        self._render_recent()

    def _require_selection(self, grouped) -> bool:
        if not grouped:
            QMessageBox.information(self, "SoliGuard", "처리할 행을 선택하세요.")
            return False
        return True

    def save_report(self):
        if not self.file_results:
            QMessageBox.information(self, "SoliGuard", "먼저 점검을 실행하세요.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "리포트 저장", "soliguard_report.pdf", "PDF (*.pdf)")
        if not path:
            return
        try:
            generate_pdf_report(self.file_results, self.profile, Path(path))
            QMessageBox.information(self, "리포트 저장", f"저장됨: {path}")
        except ReportError as e:
            QMessageBox.warning(self, "리포트 생성 실패", str(e))

    def run_figma_scan(self, url: str, token: str, consent: bool):
        from .figma_scan import (
            FigmaApiError, FigmaConsentError, parse_file_key, scan_figma_file,
        )

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


# 감사 로그/표시 유틸 -------------------------------------------------------
_ACTION_KO = {
    "mask": "마스킹", "quarantine": "격리", "restore": "복원",
    "delete": "완전삭제", "figma_scan": "Figma 검사",
}


def _read_audit_tail(n: int) -> list[dict]:
    """감사 로그 마지막 n줄을 dict 리스트로(최신이 마지막)."""
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
    fonts.load_fonts(app)            # Pretendard 등록·적용
    app.setWindowIcon(icons.app_icon())
    app.setStyleSheet(build_qss("light"))
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
