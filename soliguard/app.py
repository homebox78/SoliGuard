"""앱 진입점 - 온보딩 분기, 테마 적용, 시스템 트레이 상주.

설치형 데스크톱 앱의 생애주기를 구현한다:
    최초 실행 → 온보딩 → 메인 윈도우 + 트레이 상주(창 닫아도 종료 안 됨).

실행:  py -m soliguard.app   (PySide6 설치 필요)
"""

from __future__ import annotations

import os
import sys

from PySide6.QtGui import QAction, QColor, QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from .config import CONFIG_FILE, DATA_DIR, AppConfig
from .gui import MainWindow
from .theme import build_qss

GRADE_COLOR = {"safe": "#16A34A", "warn": "#D97706", "danger": "#DC2626"}
GRADE_LABEL = {"safe": "안전", "warn": "주의", "danger": "위험"}


def _grade_icon(grade_key: str) -> QIcon:
    """위험 등급 색의 트레이 아이콘 생성."""
    pix = QPixmap(16, 16)
    pix.fill(QColor(GRADE_COLOR.get(grade_key, "#64748B")))
    return QIcon(pix)


class SoliGuardApp:
    def __init__(self):
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.cfg = AppConfig.load()
        self.app.setStyleSheet(build_qss(self.cfg.theme))
        self.window: MainWindow | None = None
        self.tray: QSystemTrayIcon | None = None
        self.wizard = None

        if not CONFIG_FILE.exists():
            self._run_onboarding()
        else:
            self._launch_main()

    # ---- 온보딩 ----
    def _run_onboarding(self):
        from .onboarding import OnboardingWizard

        self.wizard = OnboardingWizard()
        self.wizard.completed.connect(self._on_onboarded)
        self.wizard.show()

    def _on_onboarded(self, cfg: AppConfig):
        self.cfg = cfg
        if cfg.schedule.enabled:
            try:
                from .scheduler import register_windows_task

                register_windows_task(cfg)
            except Exception:
                pass
        self._launch_main()

    # ---- 메인 + 트레이 ----
    def _launch_main(self):
        self.window = MainWindow(cfg=self.cfg)
        self.window.scan_finished.connect(self._on_scan_finished)
        self._setup_tray()
        self.window._tray_active = self.tray is not None
        self.window.show()

    def _setup_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QSystemTrayIcon(_grade_icon(self.cfg.last_grade), self.app)
        self.tray.setToolTip("SoliGuard")
        menu = QMenu()

        act_scan = QAction("지금 점검", self.app)
        act_scan.triggered.connect(self.window.start_scan)
        act_report = QAction("마지막 리포트 열기", self.app)
        act_report.triggered.connect(self._open_last_report)
        act_show = QAction("창 열기", self.app)
        act_show.triggered.connect(self._show_window)
        act_quit = QAction("종료", self.app)
        act_quit.triggered.connect(self._quit)

        for a in (act_scan, act_report):
            menu.addAction(a)
        menu.addSeparator()
        menu.addAction(act_show)
        menu.addAction(act_quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_clicked)
        self.tray.show()

    def _on_scan_finished(self, grade_key: str):
        self.cfg.last_grade = grade_key
        self.cfg.save()
        if self.tray:
            self.tray.setIcon(_grade_icon(grade_key))
            self.tray.showMessage(
                "SoliGuard",
                f"점검 완료 — 위험 등급: {GRADE_LABEL.get(grade_key, grade_key)}",
            )

    def _on_tray_clicked(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self._show_window()

    def _show_window(self):
        if self.window:
            self.window.showNormal()
            self.window.activateWindow()

    def _open_last_report(self):
        reports = sorted(DATA_DIR.glob("report_*.pdf"))
        if reports and hasattr(os, "startfile"):
            os.startfile(str(reports[-1]))  # type: ignore[attr-defined]  # Windows
        else:
            QMessageBox.information(
                self.window, "SoliGuard", "아직 생성된 리포트가 없습니다."
            )

    def _quit(self):
        if self.tray:
            self.tray.hide()
        self.app.quit()

    def run(self) -> int:
        # 창을 닫아도 트레이로 상주(트레이 사용 가능할 때만)
        self.app.setQuitOnLastWindowClosed(self.tray is None)
        return self.app.exec()


def main() -> int:
    return SoliGuardApp().run()


if __name__ == "__main__":
    raise SystemExit(main())
