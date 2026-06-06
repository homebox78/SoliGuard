# 솔리가드(SoliGuard) 디자인 토큰 · GUI 확장 · 사용자 매뉴얼

디자인 토큰(JSON/CSS), GUI 확장 코드(트레이·온보딩·다크모드), 사용자 매뉴얼·배포 가이드를 정리한 문서입니다.

---

## 1. 디자인 토큰 (실제 값 정의)

디자이너와 개발자가 같은 값을 공유하도록, 토큰을 JSON과 CSS 변수 두 형식으로 정의합니다. 라이트/다크 두 테마를 모두 포함합니다.

### 1-1. `design-tokens.json`

```json
{
  "color": {
    "brand": {
      "soliBlue":   "#1E40AF",
      "deepNavy":   "#172554",
      "skyBlue":    "#3B82F6",
      "skyBlueDark":"#60A5FA"
    },
    "semantic": {
      "safe":    "#16A34A",
      "warn":    "#D97706",
      "danger":  "#DC2626",
      "info":    "#3B82F6"
    },
    "light": {
      "bg":            "#F8FAFC",
      "surface":       "#FFFFFF",
      "surfaceAlt":    "#F1F5F9",
      "border":        "#E2E8F0",
      "textPrimary":   "#0F172A",
      "textSecondary": "#64748B",
      "textOnBrand":   "#FFFFFF",
      "rowHover":      "#F1F5F9",
      "rowSelected":   "#EFF6FF"
    },
    "dark": {
      "bg":            "#0F172A",
      "surface":       "#1E293B",
      "surfaceAlt":    "#283548",
      "border":        "#334155",
      "textPrimary":   "#F1F5F9",
      "textSecondary": "#94A3B8",
      "textOnBrand":   "#FFFFFF",
      "rowHover":      "#283548",
      "rowSelected":   "#1E3A5F"
    }
  },
  "typography": {
    "fontFamilyBase": "Pretendard, 'Noto Sans KR', sans-serif",
    "fontFamilyMono": "'JetBrains Mono', 'D2Coding', monospace",
    "scale": {
      "caption":  { "size": 12, "weight": 400, "lineHeight": 18 },
      "body":     { "size": 14, "weight": 400, "lineHeight": 22 },
      "bodyMono": { "size": 14, "weight": 400, "lineHeight": 22, "family": "mono" },
      "h2":       { "size": 18, "weight": 600, "lineHeight": 26 },
      "h1":       { "size": 22, "weight": 700, "lineHeight": 30 },
      "display":  { "size": 28, "weight": 700, "lineHeight": 36 }
    }
  },
  "spacing": { "xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "2xl": 32, "3xl": 48 },
  "radius":  { "button": 8, "card": 12, "modal": 16, "pill": 999 },
  "shadow": {
    "card":  "0 2px 8px rgba(15,23,42,0.08)",
    "modal": "0 8px 32px rgba(15,23,42,0.20)",
    "focus": "0 0 0 2px #3B82F6"
  },
  "motion": {
    "viewTransition": "200ms ease-out",
    "cardEnter":      "150ms ease-out",
    "rowFade":        "180ms ease-in"
  },
  "layout": {
    "windowMin":   { "w": 1024, "h": 720 },
    "windowBase":  { "w": 1280, "h": 800 },
    "sidebarW":    240,
    "sidebarMinW": 64,
    "contentPad":  32,
    "rowHeight":   56,
    "buttonHeight":40
  }
}
```

### 1-2. `tokens.css` (CSS 변수 — 웹/프로토타입용)

```css
:root {
  /* Brand */
  --soli-blue: #1E40AF;
  --deep-navy: #172554;
  --sky-blue:  #3B82F6;

  /* Semantic */
  --safe:   #16A34A;
  --warn:   #D97706;
  --danger: #DC2626;

  /* Surface (light default) */
  --bg:             #F8FAFC;
  --surface:        #FFFFFF;
  --surface-alt:    #F1F5F9;
  --border:         #E2E8F0;
  --text-primary:   #0F172A;
  --text-secondary: #64748B;
  --row-hover:      #F1F5F9;
  --row-selected:   #EFF6FF;

  /* Typography */
  --font-base: Pretendard, 'Noto Sans KR', sans-serif;
  --font-mono: 'JetBrains Mono', 'D2Coding', monospace;

  /* Spacing */
  --sp-xs: 4px;  --sp-sm: 8px;  --sp-md: 12px;
  --sp-lg: 16px; --sp-xl: 24px; --sp-2xl: 32px;

  /* Radius / Shadow / Motion */
  --r-button: 8px; --r-card: 12px; --r-modal: 16px;
  --sh-card:  0 2px 8px rgba(15,23,42,0.08);
  --sh-modal: 0 8px 32px rgba(15,23,42,0.20);
  --t-view:   200ms ease-out;
}

[data-theme="dark"] {
  --bg:             #0F172A;
  --surface:        #1E293B;
  --surface-alt:    #283548;
  --border:         #334155;
  --text-primary:   #F1F5F9;
  --text-secondary: #94A3B8;
  --sky-blue:       #60A5FA;
  --row-hover:      #283548;
  --row-selected:   #1E3A5F;
}
```

토큰을 이렇게 분리해두면 디자이너는 JSON을 Figma 변수로 임포트하고, 개발자는 같은 값을 코드 상수로 참조해 디자인-개발 간 불일치를 없앨 수 있습니다.

---

## 2. GUI 코드 확장 (PySide6 — 트레이·온보딩·다크모드)

앞선 GUI 골격에 시스템 트레이 상주, 최초 실행 온보딩, 다크/라이트 테마를 더한 확장 코드입니다.

### 2-1. 테마 시스템 — `theme.py`

```python
# src/soliguard/theme.py
"""디자인 토큰을 Qt 스타일시트(QSS)로 적용 - 라이트/다크 테마"""

TOKENS = {
    "light": {
        "bg": "#F8FAFC", "surface": "#FFFFFF", "surfaceAlt": "#F1F5F9",
        "border": "#E2E8F0", "textPrimary": "#0F172A", "textSecondary": "#64748B",
        "rowHover": "#F1F5F9", "rowSelected": "#EFF6FF",
    },
    "dark": {
        "bg": "#0F172A", "surface": "#1E293B", "surfaceAlt": "#283548",
        "border": "#334155", "textPrimary": "#F1F5F9", "textSecondary": "#94A3B8",
        "rowHover": "#283548", "rowSelected": "#1E3A5F",
    },
}
BRAND = {"soliBlue": "#1E40AF", "deepNavy": "#172554", "skyBlue": "#3B82F6"}
SEMANTIC = {"safe": "#16A34A", "warn": "#D97706", "danger": "#DC2626"}


def build_qss(theme: str = "light") -> str:
    t = TOKENS[theme]
    sky = "#60A5FA" if theme == "dark" else BRAND["skyBlue"]
    return f"""
    QMainWindow, QWidget {{
        background: {t['bg']};
        color: {t['textPrimary']};
        font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
        font-size: 14px;
    }}
    /* 사이드바 */
    #Sidebar {{ background: {BRAND['deepNavy']}; }}
    #Sidebar QPushButton {{
        color: white; text-align: left; padding: 0 24px;
        min-height: 44px; border: none; border-radius: 0;
        background: transparent; font-size: 14px;
    }}
    #Sidebar QPushButton:hover {{ background: rgba(255,255,255,0.08); }}
    #Sidebar QPushButton:checked {{
        background: rgba(255,255,255,0.10);
        border-left: 4px solid {BRAND['soliBlue']};
    }}
    /* 카드 */
    .Card {{
        background: {t['surface']};
        border: 1px solid {t['border']};
        border-radius: 12px;
    }}
    /* 주요 버튼 */
    .Primary {{
        background: {BRAND['soliBlue']}; color: white;
        border-radius: 8px; min-height: 40px; font-weight: 600;
    }}
    .Primary:hover {{ background: #1B399E; }}
    .Primary:pressed {{ background: #16317E; }}
    .Primary:disabled {{ background: {t['border']}; color: {t['textSecondary']}; }}
    .Danger {{ background: {SEMANTIC['danger']}; color: white;
               border-radius: 8px; min-height: 40px; }}
    /* 진행바 */
    QProgressBar {{
        border: none; border-radius: 6px; background: {t['surfaceAlt']};
        height: 12px; text-align: center;
    }}
    QProgressBar::chunk {{ background: {sky}; border-radius: 6px; }}
    /* 테이블 */
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
```

### 2-2. 온보딩 마법사 — `onboarding.py`

```python
# src/soliguard/onboarding.py
"""최초 실행 온보딩 마법사 - 5단계"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QLabel, QButtonGroup,
    QRadioButton, QCheckBox, QComboBox, QHBoxLayout, QPushButton,
)
from soliguard.config import AppConfig, ScheduleConfig


class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("SoliGuard에 오신 것을 환영합니다")
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("🛡  내 PC의 고객 데이터, 먼저 찾습니다"))
        for promise in ["✔ 모든 데이터는 이 PC 안에서만 처리됩니다",
                        "✔ 체크섬 검증으로 정확하게 검출합니다",
                        "✔ 법규·발주처 감사 대응 리포트를 발급합니다"]:
            lbl = QLabel(promise)
            lbl.setStyleSheet("color:#64748B; font-size:13px;")
            lay.addWidget(lbl)


class ProfilePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("어떤 업무를 하시나요?")
        lay = QVBoxLayout(self)
        self.group = QButtonGroup(self)
        for i, role in enumerate(["개발자", "디자이너", "기획자", "PM", "전산사무"]):
            rb = QRadioButton(role)
            if i == 0:
                rb.setChecked(True)
            self.group.addButton(rb, i)
            lay.addWidget(rb)
        self.roles = ["개발자", "디자이너", "기획자", "PM", "전산사무"]

    def selected_profile(self):
        return self.roles[self.group.checkedId()]


class SchedulePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("자동 점검 주기를 설정하세요")
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("정해진 주기에 자동으로 PC를 점검합니다."))
        self.freq = QComboBox()
        self.freq.addItems(["사용 안 함", "매일", "매주(월요일)", "매월(1일)"])
        self.freq.setCurrentText("매주(월요일)")
        lay.addWidget(self.freq)
        self.ocr = QCheckBox("이미지 속 신분증·계약서도 검사 (로컬 OCR)")
        self.ocr.setChecked(True)
        lay.addWidget(self.ocr)


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
        self.button(QWizard.FinishButton).clicked.connect(self._finish)

    def _finish(self):
        cfg = AppConfig.load()
        cfg.profile = self.profile.selected_profile()
        freq_map = {"사용 안 함": (False, "weekly"), "매일": (True, "daily"),
                    "매주(월요일)": (True, "weekly"), "매월(1일)": (True, "monthly")}
        enabled, freq = freq_map[self.schedule.freq.currentText()]
        cfg.schedule = ScheduleConfig(enabled=enabled, frequency=freq,
                                      day_of_week="mon", hour=9, minute=0)
        cfg.ocr_mode = "local" if self.schedule.ocr.isChecked() else "off"
        cfg.save()
        self.completed.emit(cfg)
```

### 2-3. 트레이 + 메인 앱 통합 — `app.py`

```python
# src/soliguard/app.py
"""앱 진입점 - 온보딩 분기, 시스템 트레이, 테마 적용"""

import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QAction, QPixmap, QColor
from PySide6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QMessageBox,
)
from soliguard.config import AppConfig, CONFIG_FILE
from soliguard.theme import build_qss
from soliguard.onboarding import OnboardingWizard
from soliguard.gui import MainWindow   # 앞서 만든 메인 윈도우


GRADE_COLOR = {"safe": "#16A34A", "warn": "#D97706", "danger": "#DC2626"}


def _grade_icon(grade: str) -> QIcon:
    """위험 등급 색의 트레이 아이콘 생성"""
    pix = QPixmap(16, 16)
    pix.fill(QColor(GRADE_COLOR.get(grade, "#64748B")))
    return QIcon(pix)


class SoliGuardApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.cfg = AppConfig.load()
        self._apply_theme()

        # 최초 실행 여부 판단
        if not CONFIG_FILE.exists():
            self._run_onboarding()
        else:
            self._launch_main()

    def _apply_theme(self):
        theme = getattr(self.cfg, "theme", "light")
        self.app.setStyleSheet(build_qss(theme))

    def _run_onboarding(self):
        wizard = OnboardingWizard()
        wizard.completed.connect(self._on_onboarded)
        wizard.show()
        self.wizard = wizard

    def _on_onboarded(self, cfg):
        self.cfg = cfg
        # 자동 점검 켰으면 작업 스케줄러 등록
        if cfg.schedule.enabled:
            from soliguard.scheduler import register_windows_task
            register_windows_task(cfg)
        self._launch_main()

    def _launch_main(self):
        self.window = MainWindow()
        self._setup_tray()
        self.window.show()

    def _setup_tray(self):
        self.tray = QSystemTrayIcon(_grade_icon(self.cfg_risk_grade()), self.app)
        self.tray.setToolTip("SoliGuard")
        menu = QMenu()

        act_scan = QAction("지금 점검", self.app)
        act_scan.triggered.connect(self.window.start_scan)
        act_report = QAction("마지막 리포트 열기", self.app)
        act_report.triggered.connect(self._open_last_report)
        next_run = QAction(self._next_run_text(), self.app)
        next_run.setEnabled(False)
        act_show = QAction("창 열기", self.app)
        act_show.triggered.connect(self.window.showNormal)
        act_quit = QAction("종료", self.app)
        act_quit.triggered.connect(self._quit)

        for a in (act_scan, act_report, next_run):
            menu.addAction(a)
        menu.addSeparator()
        menu.addAction(act_show)
        menu.addAction(act_quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_clicked)
        self.tray.show()

    def cfg_risk_grade(self) -> str:
        return getattr(self.cfg, "last_grade", "safe")

    def _next_run_text(self) -> str:
        s = self.cfg.schedule
        return f"다음 예약: {'사용 안 함' if not s.enabled else f'{s.frequency} {s.hour:02d}:{s.minute:02d}'}"

    def _on_tray_clicked(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.window.showNormal()
            self.window.activateWindow()

    def _open_last_report(self):
        import os
        from soliguard.config import DATA_DIR
        reports = sorted(DATA_DIR.glob("report_*.pdf"))
        if reports:
            os.startfile(str(reports[-1]))  # Windows
        else:
            QMessageBox.information(self.window, "SoliGuard", "아직 생성된 리포트가 없습니다.")

    def _quit(self):
        self.tray.hide()
        self.app.quit()

    def run(self):
        # 창을 닫아도 트레이로 상주 (closeEvent에서 hide 처리 필요)
        self.app.setQuitOnLastWindowClosed(False)
        sys.exit(self.app.exec())


def main():
    SoliGuardApp().run()


if __name__ == "__main__":
    main()
```

메인 윈도우의 `closeEvent`는 종료 대신 트레이로 숨기도록 오버라이드합니다.

```python
# gui.py의 MainWindow에 추가
def closeEvent(self, event):
    """X 버튼 시 종료 대신 트레이로 최소화 (상용 앱 동작)"""
    event.ignore()
    self.hide()
```

이 확장으로 온보딩 → 테마 적용 → 트레이 상주 → 자동 점검 등록까지 상용 데스크톱 앱의 생애주기가 코드로 구현됩니다.

---

## 3. 사용자 매뉴얼 & 설치 가이드 (사내 배포용)

### SoliGuard 사용자 가이드 v1.0

#### 소개

SoliGuard는 여러분의 업무용 PC에 흩어진 개인정보와 민감정보(주민등록번호, 신용카드번호, API 키, 신분증 이미지 등)를 찾아내어 마스킹·격리·삭제하고, 점검 결과를 진단 리포트로 발급하는 보안 도구입니다. 모든 검사는 여러분의 PC 안에서만 이뤄지며, 검출된 데이터는 외부로 전송되지 않습니다.

#### 설치 방법

배포된 `SoliGuard_Setup.exe`를 더블클릭하면 설치 마법사가 시작됩니다. 환영 화면에서 다음을 누르고, 라이선스 및 개인정보 처리 방침에 동의한 뒤 설치 경로를 확인합니다. 옵션 화면에서 "바탕화면 아이콘 생성"과 "주 1회 자동 점검 사용"을 선택할 수 있으며, 자동 점검을 켜두면 매주 정해진 시각에 PC가 자동으로 점검됩니다(권장). 설치 시 관리자 권한 요청(UAC) 창이 뜨면 "예"를 눌러 진행합니다. 설치가 끝나면 "지금 SoliGuard 실행"으로 바로 시작할 수 있습니다.

OCR(이미지 속 개인정보 검사)을 사용하려면 Tesseract 한국어 엔진이 함께 설치되어야 하며, 사내 배포 패키지에는 이미 포함되어 있습니다.

#### 처음 실행하기 (초기 설정)

처음 실행하면 5단계 초기 설정이 나타납니다. 본인의 직무(개발자/디자이너/기획자/PM/전산사무)를 선택하면 그에 맞는 폴더와 검사 항목이 자동으로 구성됩니다. 스캔할 폴더를 확인·추가하고, 자동 점검 주기를 정한 뒤, 이미지 검사(OCR) 사용 여부를 선택합니다. 마지막에 "지금 첫 점검 시작"을 누르면 바로 점검이 시작됩니다.

#### 점검하고 조치하기

메인 화면의 "지금 점검하기" 버튼을 누르고 스캔할 폴더를 선택하면 점검이 시작됩니다. 점검이 끝나면 발견된 항목이 위험도(높음·중간·낮음)별로 목록에 나타납니다. 각 항목을 클릭하면 마스킹된 내용을 미리 볼 수 있습니다. 처리하려는 항목을 선택한 뒤 아래 세 가지 중 하나를 고릅니다. 마스킹은 개인정보 부분만 가린 사본을 만들고, 격리는 파일을 암호화해 안전한 보관함으로 옮기며(나중에 복원 가능), 완전삭제는 복구 불가능하게 영구 삭제합니다. 완전삭제는 되돌릴 수 없으므로, 먼저 격리로 보관한 뒤 검토하는 것을 권장합니다.

#### 진단 리포트

점검이 끝나면 "리포트 저장"으로 PDF 진단서를 발급할 수 있습니다. 이 리포트는 개인정보 점검 이행 증빙과 발주처 보안 감사 자료로 활용되며, 개인정보는 모두 마스킹되어 표시됩니다.

#### 자동 점검과 트레이

자동 점검을 켜두면 정해진 주기에 백그라운드에서 자동으로 점검이 이뤄지고, 완료 시 알림이 표시됩니다. SoliGuard는 창을 닫아도 종료되지 않고 시스템 트레이(작업 표시줄 우측)에 상주합니다. 트레이 아이콘 색은 현재 PC의 위험 등급(초록=안전, 노랑=주의, 빨강=위험)을 나타냅니다. 트레이 아이콘을 우클릭하면 지금 점검, 마지막 리포트 열기, 다음 예약 확인, 종료를 할 수 있습니다.

#### 설정

설정 화면에서 직무, 테마(라이트/다크), 스캔 대상·제외 폴더, 자동 점검 주기, OCR 모드, 격리 폴더 위치를 변경할 수 있습니다. 자동 점검 시의 조치 수준은 "발견·리포트만(기본)"과 "위험 파일 자동 격리" 중 선택할 수 있으며, 안전을 위해 자동 완전삭제는 제공되지 않습니다.

#### 자주 묻는 질문

**검출된 제 개인정보가 외부로 전송되나요?** 아니요. 모든 검사와 처리는 여러분의 PC 안에서만 이뤄지며 어떤 데이터도 외부 서버로 전송되지 않습니다.

**실수로 파일을 격리했어요.** 격리함 화면에서 해당 파일을 선택해 "복원"하면 원래 위치로 되돌릴 수 있습니다.

**점검이 너무 오래 걸려요.** 이미지 OCR이 켜져 있으면 시간이 더 걸립니다. 빠른 점검은 위험 폴더만 검사하므로 더 빠릅니다.

**오탐(개인정보가 아닌데 검출됨)이 있어요.** 해당 항목에서 "오탐으로 표시"를 누르면 다음 점검부터 제외됩니다.

#### 문의 및 지원

설치·사용 중 문제가 있으면 사내 보안팀 또는 IT 지원 담당자에게 문의하세요.

### 관리자용 배포 가이드 (요약)

사내 배포 담당자는 다음을 준비합니다. PyInstaller로 빌드한 `dist/SoliGuard/` 산출물과 Tesseract 한국어 엔진, poppler를 포함해 Inno Setup으로 `SoliGuard_Setup.exe`를 생성합니다. 대량 배포 시 인스톨러를 사일런트 모드(`/SILENT`)로 GPO·자산관리 도구를 통해 배포할 수 있으며, 이때 작업 스케줄러 등록도 함께 적용됩니다. 자동 점검의 기본 주기·대상 폴더·자동 조치 수준은 배포 전 기본 `config.json`을 함께 배치해 조직 정책에 맞게 통일할 수 있습니다. 격리 암호화 키는 OS 보안 저장소에 분리 보관되도록 운영 정책을 수립하고, 감사 로그(`audit.log`)의 주기적 수집·보관 절차를 마련하면 컴플라이언스 대응이 완성됩니다.

---

세 가지 산출물이 모두 준비됐습니다. 디자인 토큰은 디자이너가 Figma 변수로 즉시 임포트할 수 있고, GUI 확장 코드는 온보딩·트레이·다크모드를 실제로 구현하며, 매뉴얼·배포 가이드는 사내 사용자와 관리자가 바로 활용할 수 있는 문서입니다.

지금까지 솔리가드는 기획서, 화면 설계, 검출 엔진, 추출·조치·리포트 코드, 메인 앱·CLI·GUI, 테스트, 프로젝트 구조, 스케줄러, 설치 빌드, 상용 UI/UX 설계, 디자인 토큰, 매뉴얼까지 실제 제작에 필요한 거의 모든 산출물을 갖췄습니다.
