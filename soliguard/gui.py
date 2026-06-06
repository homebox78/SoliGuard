"""PySide6 GUI - 온보딩 이후의 일상 사용 흐름.

대시보드 → 스캔 진행 → 검출 결과 → 조치/리포트 화면을 QStackedWidget 으로 전환한다.
스캔은 별도 스레드(ScanWorker)에서 돌려 UI가 멈추지 않게 한다(화면설계서: 진행 가시성).

실행:  py -m soliguard.gui   (PySide6 설치 필요: pip install PySide6)

이 모듈은 PySide6 에 의존하므로 데모/테스트 환경에 PySide6 가 없으면 import 시점에
실패한다. 순수 로직(테마 QSS·등급 매핑)은 soliguard.theme 에 분리해 두었다.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QFrame, QHBoxLayout, QHeaderView,
    QInputDialog, QLabel, QMainWindow, QMessageBox, QProgressBar, QPushButton,
    QStackedWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from .engine import PROFILE_ROLE, run_scan
from .report import ReportError, generate_pdf_report
from .theme import GRADE_DISPLAY, build_qss


class ScanWorker(QThread):
    """스캔을 백그라운드에서 실행. 진행률/완료를 시그널로 전달."""

    progress = Signal(int, int, str)   # done, total, current_path
    finished_scan = Signal(object)     # engine.ScanSummary

    def __init__(self, folders: list[Path], role: str | None, ocr_enabled: bool):
        super().__init__()
        self.folders = folders
        self.role = role
        self.ocr_enabled = ocr_enabled
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        summary = run_scan(
            self.folders,
            role=self.role,
            ocr_enabled=self.ocr_enabled,
            progress_cb=lambda i, t, p: self.progress.emit(i, t, p),
            should_stop=lambda: self._stop,
        )
        self.finished_scan.emit(summary)


class MainWindow(QMainWindow):
    scan_finished = Signal(str)  # risk_grade_key ("safe"/"warn"/"danger")

    def __init__(self, cfg=None):
        super().__init__()
        self.setWindowTitle("SoliGuard")
        self.resize(1280, 800)
        self.cfg = cfg
        self.profile = getattr(cfg, "profile", None) or "개발자"
        self.theme = getattr(cfg, "theme", None) or "light"
        self.worker: ScanWorker | None = None
        self.file_results: list = []
        self.row_index: list[tuple[Path, object]] = []  # row → (path, finding)
        self._tray_active = False  # app.py 가 트레이 상주 시 True 로 설정

        root = QWidget()
        root_lay = QHBoxLayout(root)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)
        root_lay.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        self.dashboard = self._build_dashboard()
        self.scanning = self._build_scanning()
        self.results = self._build_results()
        for w in (self.dashboard, self.scanning, self.results):
            self.stack.addWidget(w)
        root_lay.addWidget(self.stack, 1)
        self.setCentralWidget(root)
        self.stack.setCurrentWidget(self.dashboard)

    # ---- 사이드바 ----
    def _build_sidebar(self) -> QWidget:
        side = QWidget()
        side.setObjectName("Sidebar")
        side.setFixedWidth(240)
        lay = QVBoxLayout(side)
        lay.setContentsMargins(0, 16, 0, 16)
        title = QLabel("  🛡  SoliGuard")
        title.setStyleSheet("font-size:18px; font-weight:600; padding:16px 24px;")
        lay.addWidget(title)

        self.profile_box = QComboBox()
        self.profile_box.addItems(list(PROFILE_ROLE.keys()))
        if self.profile in PROFILE_ROLE:
            self.profile_box.setCurrentText(self.profile)
        self.profile_box.currentTextChanged.connect(self._on_profile_changed)
        self.profile_box.setStyleSheet("margin:0 24px;")
        lay.addWidget(QLabel("  직무"))
        lay.addWidget(self.profile_box)
        lay.addStretch()

        theme_btn = QPushButton("🌗  테마 전환")
        theme_btn.clicked.connect(self._toggle_theme)
        lay.addWidget(theme_btn)
        return side

    # ---- 대시보드 ----
    def _build_dashboard(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(32, 32, 32, 32)

        card = QFrame()
        card.setObjectName("Card")
        card_lay = QVBoxLayout(card)
        self.grade_label = QLabel("내 PC 위험 등급: 아직 점검하지 않음")
        self.grade_label.setStyleSheet("font-size:22px; font-weight:bold; padding:24px;")
        card_lay.addWidget(self.grade_label)
        lay.addWidget(card)

        lay.addStretch()
        scan_btn = QPushButton("🔍  지금 점검하기")
        scan_btn.setObjectName("Primary")
        scan_btn.setMinimumHeight(64)
        scan_btn.setStyleSheet("font-size:18px;")
        scan_btn.clicked.connect(self.start_scan)
        lay.addWidget(scan_btn)
        hint = QLabel("모든 데이터는 이 PC 안에서만 처리됩니다.")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color:#64748B; padding-top:8px;")
        lay.addWidget(hint)
        lay.addStretch()
        return w

    # ---- 스캔 진행 ----
    def _build_scanning(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(32, 32, 32, 32)
        lay.addStretch()
        lay.addWidget(QLabel("스캔 진행 중..."))
        self.progress_bar = QProgressBar()
        lay.addWidget(self.progress_bar)
        self.progress_path = QLabel("준비 중...")
        self.progress_path.setStyleSheet("color:#64748B;")
        lay.addWidget(self.progress_path)
        cancel = QPushButton("중지")
        cancel.clicked.connect(self._cancel_scan)
        lay.addWidget(cancel, alignment=Qt.AlignRight)
        lay.addStretch()
        return w

    # ---- 검출 결과 ----
    def _build_results(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(32, 32, 32, 32)
        self.result_title = QLabel("점검 결과")
        self.result_title.setStyleSheet("font-size:22px; font-weight:bold;")
        lay.addWidget(self.result_title)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["위험도", "파일", "검출 항목", "검출값(마스킹)"]
        )
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        lay.addWidget(self.table)

        bar = QHBoxLayout()
        for label, slot in [
            ("마스킹", self._action_mask),
            ("격리", self._action_quarantine),
            ("완전삭제", self._action_delete),
        ]:
            b = QPushButton(label)
            if label == "완전삭제":
                b.setObjectName("Danger")
            b.clicked.connect(slot)
            bar.addWidget(b)
        bar.addStretch()
        report_btn = QPushButton("📑 리포트 저장")
        report_btn.setObjectName("Primary")
        report_btn.clicked.connect(self.save_report)
        bar.addWidget(report_btn)
        back = QPushButton("← 대시보드")
        back.clicked.connect(lambda: self.stack.setCurrentWidget(self.dashboard))
        bar.addWidget(back)
        lay.addLayout(bar)
        return w

    # ---- 동작 ----
    def _on_profile_changed(self, text: str) -> None:
        self.profile = text

    def _toggle_theme(self) -> None:
        self.theme = "dark" if self.theme == "light" else "light"
        app = QApplication.instance()
        if app:
            app.setStyleSheet(build_qss(self.theme))

    def closeEvent(self, event):
        """트레이 상주 중이면 종료 대신 숨김(상용 앱 동작). 아니면 정상 종료."""
        if self._tray_active:
            event.ignore()
            self.hide()
        else:
            event.accept()

    def start_scan(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "스캔할 폴더 선택")
        if not folder:
            return
        self.stack.setCurrentWidget(self.scanning)
        self.progress_bar.setValue(0)
        self.worker = ScanWorker(
            [Path(folder)], PROFILE_ROLE.get(self.profile), ocr_enabled=True
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.finished_scan.connect(self._on_finished)
        self.worker.start()

    def _cancel_scan(self) -> None:
        if self.worker:
            self.worker.stop()

    def _on_progress(self, done: int, total: int, path: str) -> None:
        self.progress_bar.setMaximum(total or 1)
        self.progress_bar.setValue(done)
        self.progress_path.setText(f"검사 중: {path}")

    def _on_finished(self, summary) -> None:
        self.file_results = summary.file_results
        disp = GRADE_DISPLAY.get(summary.risk_grade, {})
        self.grade_label.setText(
            f"내 PC 위험 등급: {disp.get('icon', '')} {summary.risk_grade}"
        )
        self.result_title.setText(
            f"점검 결과 — 위험 {summary.total_findings}건 "
            f"(검사 {summary.scanned} / 검사불가 {summary.skipped})"
        )
        self._populate_table(summary.file_results)
        self.stack.setCurrentWidget(self.results)
        self.scan_finished.emit(summary.risk_grade_key)

    def _populate_table(self, results: list) -> None:
        self.table.setRowCount(0)
        self.row_index = []
        for r in results:
            for f in r.findings:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(f.severity.value))
                self.table.setItem(row, 1, QTableWidgetItem(str(r.path)))
                self.table.setItem(row, 2, QTableWidgetItem(f.info_type))
                self.table.setItem(row, 3, QTableWidgetItem(f.masked))
                self.row_index.append((Path(r.path), f))

    # ---- 선택된 행 → 파일별 findings ----
    def _selected_by_file(self) -> dict[Path, list]:
        grouped: dict[Path, list] = {}
        for idx in {i.row() for i in self.table.selectedIndexes()}:
            path, finding = self.row_index[idx]
            grouped.setdefault(path, []).append(finding)
        return grouped

    def _action_mask(self) -> None:
        grouped = self._selected_by_file()
        if not grouped:
            QMessageBox.information(self, "SoliGuard", "처리할 행을 선택하세요.")
            return
        from .actions import mask_in_text_file

        ok = 0
        for path, findings in grouped.items():
            if mask_in_text_file(path, findings).status == "success":
                ok += 1
        QMessageBox.information(self, "마스킹 완료", f"{ok}개 파일의 마스킹 사본 생성")

    def _action_quarantine(self) -> None:
        grouped = self._selected_by_file()
        if not grouped:
            QMessageBox.information(self, "SoliGuard", "처리할 행을 선택하세요.")
            return
        from .actions import quarantine_file

        ok = sum(
            1 for path in grouped if quarantine_file(path).status == "success"
        )
        QMessageBox.information(self, "격리 완료", f"{ok}개 파일을 암호화 격리함으로 이동")

    def _action_delete(self) -> None:
        grouped = self._selected_by_file()
        if not grouped:
            QMessageBox.information(self, "SoliGuard", "처리할 행을 선택하세요.")
            return
        text, ok = QInputDialog.getText(
            self,
            "완전 삭제 확인",
            f"선택한 {len(grouped)}개 파일을 복구 불가능하게 삭제합니다.\n"
            "되돌릴 수 없습니다. 확인을 위해 '삭제'를 입력하세요:",
        )
        if not ok or text.strip() != "삭제":
            return
        from .actions import secure_delete

        done = sum(
            1 for path in grouped
            if secure_delete(path, confirmed=True).status == "success"
        )
        QMessageBox.information(self, "삭제 완료", f"{done}개 파일을 영구 삭제했습니다.")

    def save_report(self) -> None:
        if not self.file_results:
            QMessageBox.information(self, "SoliGuard", "먼저 점검을 실행하세요.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "리포트 저장", "soliguard_report.pdf", "PDF (*.pdf)"
        )
        if not path:
            return
        try:
            generate_pdf_report(self.file_results, self.profile, Path(path))
            QMessageBox.information(self, "리포트 저장", f"저장됨: {path}")
        except ReportError as e:
            QMessageBox.warning(self, "리포트 생성 실패", str(e))


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(build_qss("light"))
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
