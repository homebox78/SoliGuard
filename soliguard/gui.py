"""PySide6 GUI - 정본(docs/app) 디자인 반영.

흰 사이드바(로고·메뉴·직무 칩) + 콘텐츠(대시보드/스캔/결과/격리함/이력/설정).
결과 화면은 좌측 위험도 필터 · 중앙 표(위험도 칩) · 우측 마스킹 미리보기 3분할.
스캔은 별도 스레드(ScanWorker)에서 실행.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QSize, QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QComboBox, QDialog, QFileDialog,
    QFrame, QGraphicsDropShadowEffect, QGridLayout, QHBoxLayout, QHeaderView,
    QInputDialog, QLabel, QLineEdit, QMainWindow, QMessageBox, QProgressBar,
    QPushButton, QScrollArea, QStackedWidget, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)
from PySide6.QtGui import QColor, QIcon

from . import fonts, icons
from .engine import PROFILE_ROLE, run_scan
from .profiles import ALL_PROFILES, PROFILE_DESC, PROFILE_ICON
from .report import ReportError, generate_pdf_report
from .theme import BRAND, GRADE_DISPLAY, SEMANTIC, SEV_CHIP, build_qss

_FREQ_ITEMS = ["사용 안 함", "매일", "매주(월요일)", "매월(1일)"]
_ACTION_KO = {"mask": "마스킹", "quarantine": "격리", "restore": "복원",
              "delete": "완전삭제", "figma_scan": "Figma 검사",
              "scan": "전체 스캔 실행", "closing": "프로젝트 클로징 점검"}

# 감사 액션 → (아이콘, 표시 제목, 분류) — 점검 이력 카드용
_HIST_META = {
    "scan": ("search", "전체 스캔 실행", "scan"),
    "closing": ("folderPlus", "프로젝트 클로징 점검", "scan"),
    "quarantine": ("lock", "격리 처리", "action"),
    "mask": ("eyeOff", "마스킹 처리", "action"),
    "delete": ("trash", "완전삭제 처리", "action"),
    "restore": ("refresh", "복원 처리", "action"),
    "figma_scan": ("image", "Figma 검사", "scan"),
}

# 검출 유형 → 행 아이콘(결과 테이블)
_TYPE_ICON = {
    "주민등록번호": "user", "외국인등록번호": "users",
    "휴대전화번호": "phone", "전화번호": "phone",
    "이메일": "mail", "신용카드번호": "card", "계좌번호": "card",
    "사업자등록번호": "fileText",
    "여권번호": "shieldCheck", "운전면허번호": "drive",
    "주소": "home", "IP 주소": "database",
    "API 키/시크릿": "key", "AWS Access Key": "key",
    "DB 접속정보": "database", "개인키(PEM)": "key",
    "법인등록번호": "fileText",
    "GitHub 토큰": "key", "Slack 토큰": "key", "Google API 키": "key",
    "Stripe 키": "key", "npm 토큰": "key", "JWT 토큰": "key",
}

# 검출 유형 → 평이한 설명(무엇인지 + 왜 위험한지). 결과 행 툴팁·미리보기에 노출.
_TYPE_DESC = {
    "주민등록번호": "가장 민감한 신원정보입니다. 유출 시 명의도용·금융사기에 악용될 수 있어 즉시 조치가 필요합니다.",
    "외국인등록번호": "외국인의 신원을 식별하는 민감정보입니다. 주민등록번호에 준해 보호해야 합니다.",
    "법인등록번호": "법인을 식별하는 등록번호입니다. 계약·금융 문서에서 함께 노출되면 위험이 커집니다.",
    "사업자등록번호": "사업체 식별번호입니다. 단독 노출 위험은 중간이나 다른 정보와 결합 시 주의가 필요합니다.",
    "신용카드번호": "결제에 직접 쓰일 수 있는 금융정보입니다. 유출 시 부정결제 위험이 큽니다.",
    "계좌번호": "예금 계좌 식별정보입니다. 예금주·연락처와 함께 노출되면 위험합니다.",
    "전화번호": "개인 연락처입니다. 스팸·피싱·본인확인 우회에 악용될 수 있습니다.",
    "휴대전화번호": "개인 연락처입니다. 스팸·피싱·본인확인 우회에 악용될 수 있습니다.",
    "이메일": "개인 식별·연락 수단입니다. 계정 탈취·피싱의 출발점이 될 수 있습니다.",
    "여권번호": "국제 신원증명 번호입니다. 유출 시 위·변조 및 명의도용에 악용될 수 있습니다.",
    "운전면허번호": "신분증명에 쓰이는 식별번호입니다. 신원도용 위험이 있습니다.",
    "주소": "거주지 정보입니다. 다른 개인정보와 결합하면 특정 개인을 식별할 수 있습니다.",
    "IP 주소": "접속 단말·서버를 식별합니다. 단독 위험은 낮지만 내부망 정보 노출일 수 있습니다.",
    "API 키/시크릿": "시스템 접근 자격증명입니다. 유출 시 서비스 무단 접근·과금 피해가 발생할 수 있습니다.",
    "AWS Access Key": "클라우드(AWS) 접근 키입니다. 유출 시 인프라 탈취·요금 폭탄 위험이 매우 큽니다.",
    "DB 접속정보": "데이터베이스 접속 자격증명입니다. 유출 시 전체 데이터 유출로 이어질 수 있습니다.",
    "개인키(PEM)": "암호화 개인키입니다. 유출 시 서버·통신 위장 및 복호화에 악용됩니다.",
    "GitHub 토큰": "소스 저장소 접근 토큰입니다. 유출 시 코드·비밀정보 탈취 위험이 큽니다.",
    "Slack 토큰": "메신저 작업공간 접근 토큰입니다. 유출 시 대화·파일 열람 위험이 있습니다.",
    "Google API 키": "구글 서비스 접근 키입니다. 유출 시 무단 사용·과금 피해가 발생할 수 있습니다.",
    "Stripe 키": "결제 시스템 비밀 키입니다. 유출 시 결제·환불 조작 위험이 큽니다.",
    "npm 토큰": "패키지 배포 토큰입니다. 유출 시 악성 패키지 배포에 악용될 수 있습니다.",
    "JWT 토큰": "인증 세션 토큰입니다. 유출 시 사용자 계정 도용에 악용될 수 있습니다.",
}


def _type_desc(info_type: str) -> str:
    return _TYPE_DESC.get(info_type, "민감정보로 분류된 항목입니다. 노출 범위를 확인해 조치하세요.")


# ---------------------------------------------------------------- 공용 위젯
def _h1(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet("font-size:23px; font-weight:800;")
    return lbl


def _card(shadow: bool = False) -> QFrame:
    # 그림자 없이 테두리로만 구분(흰 배경 · 평면 디자인). 아이콘 박스 등에
    # 그림자가 비치지 않도록 QGraphicsDropShadowEffect는 사용하지 않는다.
    f = QFrame()
    f.setObjectName("Card")
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


class ShieldHero(QWidget):
    """방패형 위험 히어로(등급 색 채움 + 가운데 건수)."""

    def __init__(self):
        super().__init__()
        self.setFixedSize(200, 200)
        self.total = 0
        self.grade = "안전"

    def set_data(self, counts: dict, grade: str):
        self.total = sum(counts.values())
        self.grade = grade
        self.update()

    def paintEvent(self, _e):
        from .theme import grade_color
        from PySide6.QtGui import QColor, QPainter, QPainterPath
        from PySide6.QtCore import QPointF

        c = QColor(grade_color(self.grade))
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        s, ox, oy = 150, 25, 18
        path = QPainterPath()
        path.moveTo(ox + s * 0.5, oy)
        path.lineTo(ox + s, oy + s * 0.22)
        path.lineTo(ox + s, oy + s * 0.55)
        path.quadTo(QPointF(ox + s, oy + s * 0.85), QPointF(ox + s * 0.5, oy + s))
        path.quadTo(QPointF(ox, oy + s * 0.85), QPointF(ox, oy + s * 0.55))
        path.lineTo(ox, oy + s * 0.22)
        path.closeSubpath()
        p.fillPath(path, c)
        p.setPen(QColor("#FFFFFF"))
        f = self.font(); f.setPointSize(34); f.setBold(True); p.setFont(f)
        from PySide6.QtCore import QRectF
        p.drawText(QRectF(0, 64, 200, 46), Qt.AlignCenter, str(self.total))
        f.setPointSize(10); f.setBold(True); p.setFont(f)
        p.drawText(QRectF(0, 112, 200, 18), Qt.AlignCenter,
                   "안전" if self.grade == "안전" else "위험 항목")
        p.end()


class NumericHero(QWidget):
    """숫자형 위험 히어로(큰 숫자 + 높음/중간/낮음 막대)."""

    def __init__(self):
        super().__init__()
        self.setFixedSize(220, 200)
        self.counts = {"높음": 0, "중간": 0, "낮음": 0}
        self.grade = "안전"

    def set_data(self, counts: dict, grade: str):
        self.counts = counts
        self.grade = grade
        self.update()

    def paintEvent(self, _e):
        from .theme import grade_color
        from PySide6.QtGui import QColor, QPainter
        from PySide6.QtCore import QRectF

        total = sum(self.counts.values())
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setPen(QColor(grade_color(self.grade)))
        f = self.font(); f.setPointSize(46); f.setBold(True); p.setFont(f)
        p.drawText(QRectF(0, 6, 220, 56), Qt.AlignLeft | Qt.AlignVCenter, str(total))
        f.setPointSize(11); f.setBold(False); p.setFont(f)
        p.setPen(QColor("#565E6C"))
        p.drawText(QRectF(0, 60, 220, 18), Qt.AlignLeft, "위험 항목")
        mx = max(max(self.counts.values()), 1)
        y = 92
        for sev in ("높음", "중간", "낮음"):
            v = self.counts[sev]
            color = QColor(SEV_CHIP[sev][0])
            p.setPen(QColor("#565E6C"))
            f.setPointSize(10); p.setFont(f)
            p.drawText(QRectF(0, y, 30, 16), Qt.AlignLeft, sev)
            p.fillRect(QRectF(34, y + 2, 150, 9), QColor("#EFF1F4"))
            p.fillRect(QRectF(34, y + 2, 150 * v / mx, 9), color)
            p.setPen(QColor("#14161C"))
            p.drawText(QRectF(188, y, 30, 16), Qt.AlignRight, str(v))
            y += 30
        p.end()


def _mini_stat(icon: str, label: str, value: str) -> QWidget:
    w = QWidget()
    h = QHBoxLayout(w)
    h.setContentsMargins(0, 0, 0, 0)
    h.setSpacing(9)
    av = QLabel()
    av.setFixedSize(32, 32)
    av.setAlignment(Qt.AlignCenter)
    av.setStyleSheet("background:#F7F8FA; border-radius:8px;")
    av.setPixmap(icons.line_icon(icon, 16, "#565E6C"))
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


def _seg_btn_qss(on: bool) -> str:
    """통합 세그먼트 컨트롤 버튼 스타일(선택=흰 pill / 비선택=투명)."""
    if on:
        return ("QPushButton{background:#FFFFFF; color:#B0123F; border:none;"
                "border-radius:7px; padding:5px 13px; font-weight:700; font-size:12px;}")
    return ("QPushButton{background:transparent; color:#565E6C; border:none;"
            "border-radius:7px; padding:5px 13px; font-weight:700; font-size:12px;}"
            "QPushButton:hover{color:#14161C;}")


def _make_segment(items, slot):
    """연한 회색 컨테이너 안의 통합 세그먼트. items=[(key,label,icon)].

    반환: (컨테이너 QFrame, {key: QPushButton}). 스타일은 _style_segment로 갱신."""
    from PySide6.QtWidgets import QSizePolicy
    cont = QFrame(); cont.setObjectName("Seg")
    # 부모 행 높이만큼 세로로 늘어나지 않게 고정 → 상하좌우 여백 동일(3px)
    cont.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
    cont.setStyleSheet("QFrame#Seg{background:#EFF1F4; border:1px solid #E7E9EE; border-radius:9px;}")
    h = QHBoxLayout(cont); h.setContentsMargins(3, 3, 3, 3); h.setSpacing(2)
    btns = {}
    for key, label, icon in items:
        b = QPushButton(" " + label); b.setCheckable(True)
        b.setCursor(Qt.PointingHandCursor)
        b.setIconSize(QSize(14, 14))
        b.clicked.connect(lambda _=False, k=key: slot(k))
        b._seg_icon = icon
        btns[key] = b
        h.addWidget(b)
    return cont, btns


def _style_segment(btns: dict, current: str):
    for k, b in btns.items():
        on = k == current
        b.setStyleSheet(_seg_btn_qss(on))
        b.setIcon(QIcon(icons.line_icon(b._seg_icon, 14, "#B0123F" if on else "#565E6C")))


# ---------------------------------------------------------------- 스캔 워커
def _bucket_of(info_type: str) -> str:
    # 신원 식별번호(주민/외국인/여권/운전면허) — 가장 민감한 그룹
    if info_type in ("주민등록번호", "외국인등록번호", "여권번호", "운전면허번호",
                     "신분증 이미지", "실고객 샘플"):
        return "주민등록번호"
    if info_type == "신용카드번호":
        return "신용카드번호"
    if info_type in ("API 키/시크릿", "DB 접속정보", "AWS Access Key",
                     "개인키(PEM)", "IP 주소"):
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
        self._paused = False

    def stop(self):
        self._stop = True
        self._paused = False

    def toggle_pause(self) -> bool:
        self._paused = not self._paused
        return self._paused

    def run(self):
        from pathlib import Path as _P

        from .detection import DetectionEngine
        from .engine import DEFAULT_EXCLUDES, PROFILE_ROLE, ScanSummary
        from .scanner import FileScanResult, collect_files, scan_file

        from .profiles import extensions_for

        results, scanned, skipped = [], 0, 0
        buckets = {"주민등록번호": 0, "신용카드번호": 0, "API키/DB": 0,
                   "전화·이메일": 0, "기타": 0}
        # 어떤 예외가 나도 finished_scan 은 반드시 한 번 발생시켜 화면 멈춤을 막는다.
        try:
            roles = {PROFILE_ROLE[p] for p in self.profiles if p in PROFILE_ROLE}
            engine = DetectionEngine(roles=roles or None,
                                     user_whitelist=self.user_whitelist)
            # 직무 프로파일 = 검사할 파일 확장자 필터(폴더와 무관).
            exts = extensions_for(self.profiles)
            files = collect_files(self.folders, exclude=DEFAULT_EXCLUDES,
                                  extensions=exts)
            total = len(files)
            for i, fpath in enumerate(files, 1):
                while self._paused and not self._stop:
                    self.msleep(120)
                if self._stop:
                    break
                try:
                    r = scan_file(fpath, engine, ocr_enabled=self.ocr_enabled)
                except Exception as e:  # 개별 파일 오류가 스캔 전체를 멈추지 않게
                    r = FileScanResult(_P(fpath), "검사불가", error=f"처리 오류: {e}")
                results.append(r)
                if r.status == "검사불가":
                    skipped += 1
                else:
                    scanned += 1
                    for f in r.findings:
                        buckets[_bucket_of(f.info_type)] += 1
                self.progress.emit(i, total, str(fpath), dict(buckets))
        except Exception:
            pass  # 수집/엔진 초기화 실패도 부분 결과로 마무리
        finally:
            self.finished_scan.emit(
                ScanSummary(file_results=results, scanned=scanned, skipped=skipped))


class _ScanRing(QWidget):
    """스캔 진행 원형 게이지(정본 06). 가운데 %·라벨·발견 건수."""

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(240)
        self._pct = 0
        self._found = 0
        self._stage = "준비 중"

    def set(self, pct: int, found: int, stage: str):
        self._pct = pct; self._found = found; self._stage = stage
        self.update()

    def paintEvent(self, e):
        from PySide6.QtCore import QRectF
        from PySide6.QtGui import QColor, QFont, QPainter, QPen
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        size = min(self.width(), self.height()) - 24
        x = (self.width() - size) / 2
        y = (self.height() - size) / 2
        rect = QRectF(x, y, size, size)
        pen = QPen(QColor("#F1DCE3")); pen.setWidth(16); pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen); p.drawArc(rect, 0, 360 * 16)
        pen2 = QPen(QColor(BRAND["brand"])); pen2.setWidth(16); pen2.setCapStyle(Qt.RoundCap)
        p.setPen(pen2); p.drawArc(rect, 90 * 16, -int(360 * 16 * self._pct / 100))
        p.setPen(QColor("#B0123F"))
        f = QFont(); f.setPixelSize(40); f.setBold(True); p.setFont(f)
        p.drawText(rect, Qt.AlignCenter, f"{self._pct}%")
        p.setPen(QColor("#565E6C"))
        f2 = QFont(); f2.setPixelSize(13); p.setFont(f2)
        p.drawText(QRectF(x, y + size * 0.60, size, 22), Qt.AlignCenter, self._stage)
        p.setPen(QColor("#8B92A0")); f3 = QFont(); f3.setPixelSize(12); p.setFont(f3)
        p.drawText(QRectF(x, y + size * 0.72, size, 20), Qt.AlignCenter, f"발견 {self._found}건")
        p.end()


# ---------------------------------------------------------------- 직무 팝오버
def _checkbox_pixmap(on: bool, size: int = 20):
    """둥근 사각 체크박스 픽스맵(정본 Box sq)."""
    from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
    pm = QPixmap(size, size); pm.fill(Qt.transparent)
    p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing, True)
    p.setPen(QPen(QColor(BRAND["brand"] if on else "#D6DAE2"), 1.7))
    p.setBrush(QColor(BRAND["brand"]) if on else QColor("#FFFFFF"))
    p.drawRoundedRect(1, 1, size - 2, size - 2, 6, 6)
    if on:
        p.drawPixmap(2, 2, icons.line_icon("check", size - 4, "#FFFFFF", 3))
    p.end()
    return pm


def _icon_box_pixmap(name: str, on: bool, size: int = 34):
    """라운드 사각 안에 Lucide 아이콘(선택 시 크림슨 채움+흰 아이콘)."""
    from PySide6.QtCore import QRectF
    from PySide6.QtGui import QColor, QPainter, QPixmap
    pm = QPixmap(size, size); pm.fill(Qt.transparent)
    p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing, True)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(BRAND["brand"]) if on else QColor("#F7F8FA"))
    p.drawRoundedRect(QRectF(0, 0, size, size), 9, 9)
    ic = icons.line_icon(name, round(size * 0.55), "#FFFFFF" if on else "#565E6C", 2)
    off = (size - ic.width()) // 2
    p.drawPixmap(off, off, ic)
    p.end()
    return pm


class RolePopover(QDialog):
    """직무 프로파일 복수 선택(정본 18) — 체크박스+아이콘박스+이름·설명 카드."""

    def __init__(self, parent, profiles):
        super().__init__(parent)
        self.setWindowTitle("직무 프로파일")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.selected = list(profiles)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 16)
        lay.setSpacing(8)

        thead = QHBoxLayout(); thead.setSpacing(8)
        title = QLabel("직무 프로파일")
        title.setStyleSheet("font-size:16px; font-weight:800;")
        thead.addWidget(title)
        badge = QLabel("복수 선택")
        badge.setStyleSheet(f"background:{BRAND['pink50']}; color:{BRAND['brand']};"
                            "border-radius:9px; padding:3px 9px; font-size:11px; font-weight:700;")
        thead.addWidget(badge); thead.addStretch()
        lay.addLayout(thead)
        hint = QLabel("선택한 모든 직무의 폴더·검출 항목이 합쳐서 구성됩니다.")
        hint.setStyleSheet("color:#565E6C; font-size:12.5px;")
        lay.addWidget(hint)
        lay.addSpacing(2)

        self._cards = {}
        for role in ALL_PROFILES:
            lay.addWidget(self._role_card(role))

        foot = QHBoxLayout()
        self._count = QLabel()
        self._count.setStyleSheet("color:#8B92A0; font-size:12px;")
        foot.addWidget(self._count)
        foot.addStretch()
        apply_btn = QPushButton("적용")
        apply_btn.setObjectName("Primary")
        apply_btn.setCursor(Qt.PointingHandCursor)
        apply_btn.clicked.connect(self._apply)
        foot.addWidget(apply_btn)
        lay.addSpacing(4)
        lay.addLayout(foot)
        self._refresh_count()

    def _role_card(self, role: str) -> QPushButton:
        on = role in self.selected
        b = QPushButton(); b.setObjectName("ChkCard")
        b.setCheckable(True); b.setChecked(on)
        b.setCursor(Qt.PointingHandCursor)
        b.setMinimumHeight(54)
        b.setStyleSheet(
            "QPushButton#ChkCard{background:#fff;border:1px solid #E7E9EE;"
            "border-radius:11px;text-align:left;padding:0;}"
            "QPushButton#ChkCard:hover{border-color:#D6DAE2;}"
            f"QPushButton#ChkCard:checked{{border:1px solid {BRAND['brand']};"
            f"background:{BRAND['pink50']};}}")
        h = QHBoxLayout(b); h.setContentsMargins(12, 8, 12, 8); h.setSpacing(11)
        chk = QLabel(); chk.setFixedSize(18, 18); chk.setPixmap(_checkbox_pixmap(on, 18))
        h.addWidget(chk, 0, Qt.AlignVCenter)
        ic_name = icons.ROLE_ICON.get(role, "user")
        ibox = QLabel(); ibox.setFixedSize(30, 30)
        ibox.setPixmap(_icon_box_pixmap(ic_name, on, 30))
        h.addWidget(ibox, 0, Qt.AlignVCenter)
        col = QVBoxLayout(); col.setSpacing(1); col.setContentsMargins(0, 0, 0, 0)
        nm = QLabel(role)
        nm.setStyleSheet(f"font-weight:700; font-size:13px;"
                         f"color:{BRAND['brand'] if on else '#14161C'};")
        col.addWidget(nm)
        ds = QLabel(PROFILE_DESC.get(role, ""))
        ds.setStyleSheet("color:#565E6C; font-size:11.5px;")
        col.addWidget(ds)
        h.addLayout(col, 1)

        def toggle(checked, r=role, cb=chk, ib=ibox, name=nm, icn=ic_name):
            cb.setPixmap(_checkbox_pixmap(checked, 18))
            ib.setPixmap(_icon_box_pixmap(icn, checked, 30))
            name.setStyleSheet(f"font-weight:700; font-size:13px;"
                               f"color:{BRAND['brand'] if checked else '#14161C'};")
            self._refresh_count()
        b.toggled.connect(toggle)
        self._cards[role] = b
        return b

    def _refresh_count(self):
        n = sum(1 for b in self._cards.values() if b.isChecked())
        self._count.setText(f"{n}개 직무 선택됨")

    def _apply(self):
        sel = [r for r in ALL_PROFILES if self._cards[r].isChecked()]
        self.selected = sel or [ALL_PROFILES[0]]
        self.accept()


class DeleteConfirmDialog(QDialog):
    """완전삭제 확인 모달(시안 11). choice: 'delete' | 'quarantine' | None."""

    def __init__(self, parent, items):
        super().__init__(parent)
        self.setWindowTitle("완전삭제 확인")
        self.setModal(True)
        self.setMinimumWidth(460)
        self.choice = None
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 18)
        lay.setSpacing(12)

        hd = QHBoxLayout()
        ic = QLabel()
        ic.setFixedSize(40, 40)
        ic.setAlignment(Qt.AlignCenter)
        ic.setStyleSheet("background:#FDEAEA; border-radius:10px;")
        ic.setPixmap(icons.line_icon("trash", 20, "#B0123F"))
        hd.addWidget(ic)
        tc = QVBoxLayout(); tc.setSpacing(1)
        t = QLabel("완전삭제 확인"); t.setStyleSheet("font-size:16px; font-weight:800;")
        tc.addWidget(t)
        s = QLabel("이 작업은 되돌릴 수 없습니다"); s.setStyleSheet("color:#565E6C; font-size:12px;")
        tc.addWidget(s)
        hd.addLayout(tc); hd.addStretch()
        lay.addLayout(hd)

        desc = QLabel(f"선택한 {len(items)}건을 복구 불가능하게 영구 삭제합니다(덮어쓰기 삭제).")
        desc.setWordWrap(True); desc.setStyleSheet("font-size:13px;")
        lay.addWidget(desc)

        for name, kind in items[:6]:
            row = QFrame(); row.setObjectName("FileRow")
            row.setStyleSheet("QFrame#FileRow{background:#F7F8FA;border:1px solid #E7E9EE;border-radius:10px;}")
            rl = QHBoxLayout(row); rl.setContentsMargins(12, 9, 12, 9)
            fi = QLabel(); fi.setPixmap(icons.line_icon("fileText", 15, "#565E6C"))
            rl.addWidget(fi)
            nm = QLabel(name); nm.setStyleSheet("font-size:12.5px;")
            rl.addWidget(nm); rl.addStretch()
            kl = QLabel(kind); kl.setStyleSheet("color:#8B92A0; font-size:11.5px;")
            rl.addWidget(kl)
            lay.addWidget(row)

        warn = QLabel("권장 — 먼저 [격리]로 보관 후 검토하세요. 격리본은 언제든 복원할 수 있습니다.")
        warn.setWordWrap(True)
        warn.setStyleSheet("background:#FCEFF3; border:1px solid #F6D2DE; border-radius:10px;"
                           "color:#8A1538; padding:11px 13px; font-size:12px;")
        lay.addWidget(warn)

        lay.addWidget(QLabel("확인을 위해 '삭제'를 입력하세요"))
        self.field = QLineEdit()
        self.field.setPlaceholderText("삭제")
        self.field.textChanged.connect(self._check)
        lay.addWidget(self.field)

        foot = QHBoxLayout()
        cancel = QPushButton("취소"); cancel.setObjectName("Ghost")
        cancel.clicked.connect(self.reject)
        foot.addWidget(cancel)
        foot.addStretch()
        q = QPushButton("  격리로 변경"); q.setObjectName("Ghost")
        q.setIcon(QIcon(icons.line_icon("lock", 15, "#565E6C")))
        q.clicked.connect(lambda: (setattr(self, "choice", "quarantine"), self.accept()))
        foot.addWidget(q)
        self.del_btn = QPushButton("  영구 삭제"); self.del_btn.setObjectName("Danger")
        self.del_btn.setIcon(QIcon(icons.line_icon("trash", 15, "#FFFFFF")))
        self.del_btn.setEnabled(False)
        self.del_btn.clicked.connect(lambda: (setattr(self, "choice", "delete"), self.accept()))
        foot.addWidget(self.del_btn)
        lay.addLayout(foot)

    def _check(self, text):
        self.del_btn.setEnabled(text.strip() == "삭제")


class NoticeDialog(QDialog):
    """앱 디자인 알림 모달 — 네이티브 QMessageBox 대체.

    kind: info | success | warn | error (아이콘·색이 달라진다)."""

    _KIND = {
        "info":    ("info",        "#565E6C", "#F1F2F4"),
        "success": ("checkCircle", "#15A34A", "#E7F6EC"),
        "warn":    ("alert",       "#E08600", "#FEF3E0"),
        "error":   ("alert",       "#B0123F", "#FDEAEA"),
    }

    def __init__(self, parent, title, message, kind="info",
                 action_label=None, on_action=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(380)
        icon, color, bg = self._KIND.get(kind, self._KIND["info"])

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 18)
        lay.setSpacing(16)

        hd = QHBoxLayout(); hd.setSpacing(13)
        ic = QLabel(); ic.setFixedSize(44, 44); ic.setAlignment(Qt.AlignCenter)
        ic.setStyleSheet(f"background:{bg}; border-radius:11px;")
        ic.setPixmap(icons.line_icon(icon, 22, color, 2))
        hd.addWidget(ic, 0, Qt.AlignTop)
        tc = QVBoxLayout(); tc.setSpacing(4)
        t = QLabel(title); t.setWordWrap(True)
        t.setStyleSheet("font-size:15px; font-weight:800;")
        tc.addWidget(t)
        m = QLabel(message); m.setWordWrap(True)
        m.setStyleSheet("color:#565E6C; font-size:12.5px;")
        tc.addWidget(m)
        hd.addLayout(tc, 1)
        lay.addLayout(hd)

        foot = QHBoxLayout(); foot.addStretch()
        if action_label and on_action:
            act = QPushButton(action_label); act.setObjectName("Ghost")
            act.setCursor(Qt.PointingHandCursor)
            act.clicked.connect(lambda: (on_action(), self.accept()))
            foot.addWidget(act)
        ok = QPushButton("확인"); ok.setObjectName("Primary")
        ok.setMinimumWidth(96); ok.setCursor(Qt.PointingHandCursor)
        ok.clicked.connect(self.accept)
        foot.addWidget(ok)
        lay.addLayout(foot)


_GRADE_META = {
    "위험": ("#B0123F", "#FDEAEA"),
    "주의": ("#E08600", "#FEF3E0"),
    "안전": ("#15A34A", "#E7F6EC"),
}


class ReportPreviewDialog(QDialog):
    """진단서 미리보기(정본 13). 저장 시 PDF 발급."""

    def __init__(self, parent, file_results, profiles, scanned, grade, counts):
        super().__init__(parent)
        self.setWindowTitle("진단서 미리보기")
        self.setModal(True)
        self.setMinimumSize(580, 640)
        self._file_results = file_results
        self._profiles = profiles
        self.saved = False
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # 헤더
        hd = QFrame(); hd.setObjectName("RepHd")
        hd.setStyleSheet("QFrame#RepHd{border-bottom:1px solid #E7E9EE;}")
        hh = QHBoxLayout(hd); hh.setContentsMargins(18, 12, 14, 12); hh.setSpacing(8)
        ttl = QLabel("진단서 미리보기"); ttl.setStyleSheet("font-weight:700; font-size:13.5px;")
        hh.addWidget(ttl); hh.addStretch()
        save = QPushButton("  저장"); save.setObjectName("Primary")
        save.setIcon(QIcon(icons.line_icon("download", 14, "#fff")))
        save.setCursor(Qt.PointingHandCursor)
        save.clicked.connect(self._save)
        hh.addWidget(save)
        x = QPushButton("✕"); x.setFixedSize(32, 32)
        x.setStyleSheet(
            "QPushButton{background:transparent;border:none;color:#8B92A0;font-size:15px;}"
            "QPushButton:hover{color:#14161C;}")
        x.setCursor(Qt.PointingHandCursor); x.clicked.connect(self.reject)
        hh.addWidget(x)
        lay.addWidget(hd)

        # 종이(스크롤)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea{background:#EEF0F3;} QScrollArea>QWidget>QWidget{background:#EEF0F3;}")
        host = QWidget(); hv = QVBoxLayout(host)
        hv.setContentsMargins(22, 22, 22, 22)
        paper = QFrame(); paper.setObjectName("Paper")
        paper.setStyleSheet("QFrame#Paper{background:#fff; border:1px solid #E7E9EE; border-radius:6px;}")
        pv = QVBoxLayout(paper); pv.setContentsMargins(0, 0, 0, 0); pv.setSpacing(0)
        # 크림슨 헤더
        ph = QFrame(); ph.setObjectName("RepHead")
        ph.setStyleSheet(f"QFrame#RepHead{{background:{BRAND['brand']}; border-top-left-radius:6px; border-top-right-radius:6px;}}")
        phl = QHBoxLayout(ph); phl.setContentsMargins(22, 16, 22, 16); phl.setSpacing(10)
        sh = QLabel(); sh.setPixmap(icons.line_icon("shieldCheck", 20, "#fff")); sh.setFixedSize(20, 20)
        phl.addWidget(sh)
        pt = QLabel("솔리가드 개인정보 점검 진단서")
        pt.setStyleSheet("color:#fff; font-weight:800; font-size:15px; background:transparent;")
        phl.addWidget(pt); phl.addStretch()
        pv.addWidget(ph)
        body = QVBoxLayout(); body.setContentsMargins(22, 18, 22, 20); body.setSpacing(0)
        from datetime import datetime
        now = datetime.now()
        fmt = f"{now.year}-{now.month:02d}-{now.day:02d} {now.hour:02d}:{now.minute:02d}"
        total = sum(len(r.findings) for r in file_results)
        handled = sum(counts.values())
        # 메타 표
        meta = QGridLayout(); meta.setHorizontalSpacing(10); meta.setVerticalSpacing(4)
        def _mc(text, c3=False):
            l = QLabel(text)
            l.setStyleSheet(("color:#8B92A0;" if c3 else "color:#565E6C;") + " font-size:12px;")
            return l
        meta.addWidget(_mc("점검 일시", True), 0, 0); meta.addWidget(_mc(fmt), 0, 1)
        meta.addWidget(_mc("직무 프로파일", True), 0, 2); meta.addWidget(_mc(", ".join(profiles)), 0, 3)
        meta.addWidget(_mc("검사 파일", True), 1, 0); meta.addWidget(_mc(f"{scanned:,}개"), 1, 1)
        meta.addWidget(_mc("처리 건수", True), 1, 2); meta.addWidget(_mc(f"{handled}건"), 1, 3)
        meta.setColumnStretch(1, 1); meta.setColumnStretch(3, 1)
        body.addLayout(meta)
        body.addSpacing(14)
        # 등급 배너
        gcolor, gbg = _GRADE_META.get(grade, _GRADE_META["안전"])
        banner = QFrame(); banner.setObjectName("RepBanner")
        banner.setStyleSheet(f"QFrame#RepBanner{{background:{gbg}; border-radius:8px;}}")
        bh = QHBoxLayout(banner); bh.setContentsMargins(14, 12, 14, 12)
        bl = QLabel(f"종합 위험 등급: {grade}")
        bl.setStyleSheet(f"color:{gcolor}; font-weight:800; font-size:14px; background:transparent;")
        bh.addWidget(bl); bh.addStretch()
        br = QLabel(f"마스킹 {counts.get('mask',0)} · 격리 {counts.get('quarantine',0)} · 삭제 {counts.get('delete',0)}")
        br.setStyleSheet("color:#565E6C; font-size:12px; background:transparent;")
        bh.addWidget(br)
        body.addWidget(banner)
        body.addSpacing(16)
        dt = QLabel('검출 상세 <span style="color:#8B92A0;font-weight:400;">(개인정보는 마스킹되어 표시됩니다)</span>')
        dt.setStyleSheet("font-weight:700; font-size:12.5px;")
        body.addWidget(dt)
        body.addSpacing(8)
        for r in file_results:
            if not r.findings:
                continue
            fl = QLabel(f"📄 {r.path}  ({len(r.findings)}건)")
            fl.setStyleSheet("font-weight:600; font-size:11.5px;")
            fl.setWordWrap(True)
            body.addWidget(fl)
            for f in r.findings:
                c = SEV_CHIP.get(f.severity.value, ("#8B92A0",))[0]
                ln = f"  (line {f.line})" if getattr(f, "line", 0) else ""
                fd = QLabel(f"[{f.severity.value}] {f.info_type}: {f.masked}{ln}")
                fd.setStyleSheet(f"color:{c}; font-size:11px; font-family:'JetBrains Mono','D2Coding',monospace; padding-left:12px;")
                fd.setWordWrap(True)
                body.addWidget(fd)
            body.addSpacing(8)
        note = QLabel(
            "※ 본 진단서는 개인정보보호법 제21조·제24조·제29조 이행 점검 및 발주처 보안 감사 증빙용으로 활용됩니다.\n"
            "※ 본 점검은 사용자 PC 내에서 수행되었으며, 검출된 데이터는 외부로 전송되지 않았습니다.")
        note.setWordWrap(True)
        note.setStyleSheet("color:#8B92A0; font-size:10.5px; border-top:1px solid #E7E9EE; padding-top:12px;")
        body.addSpacing(6); body.addWidget(note)
        pv.addLayout(body)
        hv.addWidget(paper)
        scroll.setWidget(host)
        lay.addWidget(scroll, 1)

    def _save(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "리포트 저장", "soliguard_report.pdf", "PDF (*.pdf)")
        if not path:
            return
        try:
            generate_pdf_report(self._file_results, ", ".join(self._profiles), Path(path))
            self.saved = True
            self.accept()
            if self.parent():
                self.parent()._toast(f"진단서를 저장했어요 — {Path(path).name}")
        except ReportError as e:
            NoticeDialog(self, "리포트 생성 실패", str(e), "error").exec()


# ---------------------------------------------------------------- 메인 윈도우
class MainWindow(QMainWindow):
    scan_finished = Signal(str)

    def __init__(self, cfg=None):
        super().__init__()
        self.setWindowTitle("SoliGuard")
        self.setWindowIcon(icons.app_icon())
        self.resize(1003, 646)  # 기본 창 크기(이전 1180×760의 85%)
        self.cfg = cfg
        self.profile = getattr(cfg, "profile", None) or "개발자"
        self.profiles = list(getattr(cfg, "profiles", None) or [self.profile])
        self.theme = getattr(cfg, "theme", None) or "light"
        self.worker = None
        self.file_results = []
        self.row_index = []
        self._tray_active = False
        self._closing_mode = False
        self._action_counts = {"mask": 0, "quarantine": 0, "delete": 0}
        self._prev_grade = "안전"
        self._prev_total = None
        self._hero_key = "donut"

        root = QWidget(); root.setObjectName("Canvas")
        row = QHBoxLayout(root)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addWidget(self._build_sidebar())
        self.stack = QStackedWidget()
        self.dashboard = self._build_dashboard()
        self.scanning = self._build_scanning()
        self.scanconfig = self._build_scanconfig()
        self.results = self._build_results()
        self.complete = self._build_complete()
        self.quarantine = self._build_quarantine()
        self.history = self._build_history()
        self.settings = self._build_settings()
        for wdg in (self.dashboard, self.scanning, self.scanconfig, self.results,
                    self.complete, self.quarantine, self.history, self.settings):
            self.stack.addWidget(wdg)
        row.addWidget(self.stack, 1)
        self.setCentralWidget(root)
        self.stack.setCurrentWidget(self.dashboard)
        self._set_hero("donut")
        self._refresh_dashboard()
        # 모든 스크롤 viewport 투명화 — 빈 영역에 시스템/팔레트 배경(누런·회색 박스) 노출 방지
        for sa in self.findChildren(QScrollArea):
            sa.viewport().setAutoFillBackground(False)
            sa.viewport().setStyleSheet("background: transparent;")

    # -------------------------------------------------------- 사이드바
    def _build_sidebar(self) -> QWidget:
        side = QWidget()
        side.setObjectName("Sidebar")
        side.setFixedWidth(232)
        self._sidebar = side
        self._sidebar_collapsed = False
        lay = QVBoxLayout(side)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # 브랜드
        brand = QWidget()
        bl = QHBoxLayout(brand)
        bl.setContentsMargins(18, 20, 18, 16)
        bl.setSpacing(11)
        nm = QVBoxLayout()
        nm.setSpacing(2)
        _logo = icons.logo_pixmap(22, white=False)
        if _logo is not None:
            name = QLabel(); name.setPixmap(_logo)
        else:
            name = QLabel('솔리<span style="color:%s;font-weight:800;">가드</span>' % BRAND["brand"])
            name.setStyleSheet("font-size:16px; font-weight:800;")
        nm.addWidget(name)
        tag = QLabel("SoliGuard · v"
                     + getattr(__import__("soliguard"), "__version__", "1.0"))
        tag.setStyleSheet("font-size:10.5px; color:#8B92A0;")
        nm.addWidget(tag)
        bl.addLayout(nm)
        bl.addStretch()
        self._side_toggle = QPushButton()
        self._side_toggle.setObjectName("SideToggle")
        self._side_toggle.setFixedSize(28, 28)
        self._side_toggle.setCursor(Qt.PointingHandCursor)
        self._side_toggle.setIcon(QIcon(icons.line_icon("chevL", 16, "#8B92A0")))
        self._side_toggle.setToolTip("사이드바 접기")
        self._side_toggle.setStyleSheet(
            "QPushButton#SideToggle{background:transparent;border:none;border-radius:7px;}"
            "QPushButton#SideToggle:hover{background:#F1F2F4;}")
        self._side_toggle.clicked.connect(self._toggle_sidebar)
        bl.addWidget(self._side_toggle, 0, Qt.AlignTop)
        lay.addWidget(brand)

        sec = QLabel("메뉴")
        sec.setStyleSheet("font-size:10.5px; font-weight:700; color:#8B92A0; padding:6px 22px 7px;")
        lay.addWidget(sec)

        self.nav_group = QButtonGroup(self)
        self._nav_buttons = {}
        self._nav_labels = {}
        navwrap = QWidget()
        nv = QVBoxLayout(navwrap)
        nv.setContentsMargins(12, 0, 12, 0)
        nv.setSpacing(2)
        for key, label, ic in [("dashboard", "  홈", "home"),
                               ("quarantine", "  격리함", "lock"),
                               ("history", "  점검 이력", "history"),
                               ("settings", "  설정", "settings")]:
            b = QPushButton(label)
            b.setObjectName("Nav")
            b.setCheckable(True)
            b.setIcon(QIcon(icons.line_icon(ic, 18, "#565E6C")))
            b.setIconSize(QSize(18, 18))
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, k=key: self._navigate(k))
            self.nav_group.addButton(b)
            self._nav_buttons[key] = b
            self._nav_labels[key] = label
            nv.addWidget(b)
        self._nav_buttons["dashboard"].setChecked(True)
        # 격리함 카운트 배지(정본 14)
        qbtn = self._nav_buttons["quarantine"]
        self._q_badge = QLabel("0", qbtn)
        self._q_badge.setStyleSheet(
            f"background:{BRAND['brand']}; color:#fff; border-radius:3px;"
            "font-size:10.5px; font-weight:700; padding:1px 7px;")
        self._q_badge.hide()
        lay.addWidget(navwrap)

        lay.addStretch()

        trust = QLabel("데이터는 이 PC 안에서만 처리됩니다")
        trust.setStyleSheet("color:#8B92A0; font-size:11px; padding:8px 16px 4px;")
        lay.addWidget(trust)

        # 직무 칩
        chip = QFrame()
        chip.setObjectName("RoleChip")
        cl = QHBoxLayout(chip)
        cl.setContentsMargins(12, 9, 12, 9)
        av = QLabel()
        av.setFixedSize(30, 30)
        av.setAlignment(Qt.AlignCenter)
        av.setStyleSheet(f"background:{BRAND['pink100']}; border-radius:8px;")
        self._role_av = av
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
        arrow = QLabel("›"); arrow.setStyleSheet("color:#8B92A0; font-size:14px;")
        cl.addWidget(arrow)
        # 칩 전체를 클릭 가능하게: 자식은 마우스 투과 + 칩이 클릭 처리
        chip.setCursor(Qt.PointingHandCursor)
        for _c in (av, self._role_caption, self._role_value, arrow):
            _c.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        chip.mousePressEvent = lambda e: self._open_role_popover()
        wrap = QWidget()
        wl = QVBoxLayout(wrap)
        wl.setContentsMargins(12, 4, 12, 12)
        wl.addWidget(chip)
        lay.addWidget(wrap)
        self._refresh_role_chip()
        # 접기 시 숨길 텍스트성 위젯들(아이콘 메뉴만 남긴다)
        self._side_hide = [name, tag, sec, trust, wrap]
        return side

    def _toggle_sidebar(self):
        """사이드바 접기/펼치기 — 접으면 아이콘 전용 좁은 레일."""
        c = not getattr(self, "_sidebar_collapsed", False)
        self._sidebar_collapsed = c
        self._sidebar.setFixedWidth(60 if c else 232)
        for wdg in getattr(self, "_side_hide", []):
            wdg.setVisible(not c)
        for key, b in self._nav_buttons.items():
            b.setText("" if c else self._nav_labels[key])
            b.setToolTip(self._nav_labels[key].strip() if c else "")
        self._side_toggle.setIcon(
            QIcon(icons.line_icon("chevR" if c else "chevL", 16, "#8B92A0")))
        self._side_toggle.setToolTip("사이드바 펼치기" if c else "사이드바 접기")
        self._q_badge.setVisible(not c and self._q_badge.text() not in ("", "0"))
        self._position_q_badge()

    def _position_q_badge(self):
        if not hasattr(self, "_q_badge"):
            return
        b = self._nav_buttons["quarantine"]
        self._q_badge.adjustSize()
        bw = self._q_badge.width()
        self._q_badge.move(b.width() - bw - 12,
                           (b.height() - self._q_badge.height()) // 2)

    def showEvent(self, e):
        super().showEvent(e)
        self._refresh_quarantine()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._position_q_badge()

    def _refresh_role_chip(self):
        n = len(self.profiles)
        self._role_caption.setText("직무 프로파일" + (f" · {n}개" if n > 1 else ""))
        self._role_value.setText(", ".join(self.profiles))
        ic = icons.ROLE_ICON.get(self.profiles[0], "user") if n == 1 else "users"
        self._role_av.setPixmap(icons.line_icon(ic, 17, BRAND["brand"]))

    def _open_role_popover(self):
        dlg = RolePopover(self, self.profiles)
        if dlg.exec() == QDialog.Accepted:
            self.profiles = dlg.selected
            self.profile = self.profiles[0]
            self._refresh_role_chip()
            if hasattr(self, "_settings_rolebtn"):
                self._settings_rolebtn.setText("  " + ", ".join(self.profiles) + "  ▾")
                self._settings_rolebtn.setIcon(
                    QIcon(icons.line_icon(icons.ROLE_ICON.get(self.profiles[0], "user"), 15, "#B0123F")))

    def _navigate(self, key: str):
        target = {"dashboard": self.dashboard, "quarantine": self.quarantine,
                  "history": self.history, "settings": self.settings}[key]
        if key == "quarantine":
            self._refresh_quarantine()
        elif key == "history":
            self._refresh_history()
        self.stack.setCurrentWidget(target)

    def _select_nav(self, key: str):
        self._nav_buttons[key].setChecked(True)

    # -------------------------------------------------------- 대시보드
    def _build_dashboard(self) -> QWidget:
        outer = QWidget()
        ol = QVBoxLayout(outer)
        ol.setContentsMargins(32, 28, 32, 28)
        ol.setSpacing(18)
        hrow = QHBoxLayout()
        htext = QVBoxLayout()
        htext.setSpacing(3)
        ph = QLabel("보안 대시보드")
        ph.setStyleSheet("font-size:23px; font-weight:800;")
        htext.addWidget(ph)
        self.dash_sub = QLabel("아직 점검 기록이 없습니다 — 첫 점검을 시작해 보세요")
        self.dash_sub.setStyleSheet("color:#565E6C; font-size:13px;")
        htext.addWidget(self.dash_sub)
        hrow.addLayout(htext)
        hrow.addStretch()
        seglbl = QLabel("위험 표현"); seglbl.setStyleSheet("color:#8B92A0; font-size:12px;")
        hrow.addWidget(seglbl)
        hrow.addSpacing(6)
        cont, self._hero_seg = _make_segment(
            [("donut", "도넛", "refresh"), ("shield", "방패", "shield"),
             ("numeric", "숫자", "bolt")], self._set_hero)
        hrow.addWidget(cont)
        ol.addLayout(hrow)

        # 히어로 카드
        hero = _card()
        hl = QHBoxLayout(hero)
        hl.setContentsMargins(26, 22, 26, 22)
        hl.setSpacing(28)
        self.hero_stack = QStackedWidget()
        self.hero_stack.setFixedSize(224, 200)
        self.donut = DonutHero()
        self.shield_hero = ShieldHero()
        self.numeric_hero = NumericHero()
        for hw in (self.donut, self.shield_hero, self.numeric_hero):
            self.hero_stack.addWidget(hw)
        hl.addWidget(self.hero_stack)

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
        self.dash_prev = QLabel("")
        self.dash_prev.setStyleSheet("color:#15A34A; font-size:12.5px; font-weight:700;")
        self.dash_prev.setVisible(False)
        right.addWidget(self.dash_prev)
        btns = QHBoxLayout()
        scan_btn = QPushButton("  지금 점검하기")
        scan_btn.setObjectName("Primary")
        scan_btn.setMinimumHeight(46)
        scan_btn.setIcon(QIcon(icons.line_icon("search", 18, "#FFFFFF")))
        scan_btn.setIconSize(QSize(18, 18))
        scan_btn.setCursor(Qt.PointingHandCursor)
        scan_btn.clicked.connect(lambda: self._go_scanconfig("full"))
        btns.addWidget(scan_btn)
        quick_btn = QPushButton("  빠른 점검")
        quick_btn.setObjectName("Ghost")
        quick_btn.setMinimumHeight(46)
        quick_btn.setIcon(QIcon(icons.line_icon("bolt", 18, "#565E6C")))
        quick_btn.setIconSize(QSize(18, 18))
        quick_btn.clicked.connect(lambda: self._go_scanconfig("quick"))
        btns.addWidget(quick_btn)
        btns.addStretch()
        right.addSpacing(6)
        right.addLayout(btns)
        stats = QHBoxLayout()
        stats.setSpacing(18)
        self.stat_next = _mini_stat("clock", "다음 자동 점검", "사용 안 함")
        self.stat_role = _mini_stat("folder", "점검 직무", ", ".join(self.profiles))
        self.stat_quar = _mini_stat("archive", "격리 보관", "0개")
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
        cbtn = QPushButton("  클로징 점검 시작")
        cbtn.setObjectName("Ghost")
        cbtn.setIcon(QIcon(icons.line_icon("folderPlus", 17, "#565E6C")))
        cbtn.setIconSize(QSize(17, 17))
        cbtn.clicked.connect(lambda: self._go_scanconfig("closing"))
        cc.addWidget(cbtn)
        low.addWidget(closing, 2)
        ol.addLayout(low, 1)
        return outer

    def _set_hero(self, key: str):
        idx = {"donut": 0, "shield": 1, "numeric": 2}[key]
        self.hero_stack.setCurrentIndex(idx)
        self._hero_key = key
        _style_segment(self._hero_seg, key)

    def _render_recent(self):
        while self.recent_box.count():
            it = self.recent_box.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        entries = list(reversed(_read_audit_tail(6)))
        if not entries:
            e = QLabel("아직 점검 이력이 없습니다. ‘지금 점검하기’로 첫 점검을 시작하세요.")
            e.setStyleSheet("color:#8B92A0; padding:8px 0;")
            self.recent_box.addWidget(e)
            return
        for e in entries:
            self.recent_box.addWidget(self._recent_row(e))

    def _recent_row(self, e: dict) -> QWidget:
        action = e.get("action", "")
        icn, _t, kind = _HIST_META.get(action, ("fileText", _ACTION_KO.get(action, action), "action"))
        row = QWidget()
        h = QHBoxLayout(row); h.setContentsMargins(0, 5, 0, 5); h.setSpacing(11)
        tone = (BRAND["pink50"], BRAND["brand"]) if kind == "scan" else ("#F1F2F4", "#565E6C")
        box = QLabel(); box.setFixedSize(34, 34); box.setAlignment(Qt.AlignCenter)
        box.setStyleSheet(f"background:{tone[0]}; border-radius:9px;")
        box.setPixmap(icons.line_icon(icn, 17, tone[1], 2))
        h.addWidget(box)
        col = QVBoxLayout(); col.setSpacing(1)
        if action in ("scan", "closing"):
            title = f"{_ACTION_KO.get(action, action)} — 위험 {e.get('findings', 0)}건 발견"
        elif action in ("quarantine", "mask", "delete", "restore"):
            title = f"{_ACTION_KO.get(action, action)} — {Path(e.get('path','')).name}"
        else:
            title = _ACTION_KO.get(action, action)
        t = QLabel(title); t.setStyleSheet("font-weight:700; font-size:12.5px;")
        col.addWidget(t)
        ts = e.get("ts", "")
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(ts)
            ts = f"{self._rel_time(e.get('ts',''))} · {dt.month}/{dt.day} {dt.hour:02d}:{dt.minute:02d}"
        except (ValueError, TypeError):
            pass
        s = QLabel(ts); s.setStyleSheet("color:#8B92A0; font-size:11px;")
        col.addWidget(s)
        h.addLayout(col, 1)
        if e.get("profile"):
            tag = QLabel(e["profile"])
            tag.setStyleSheet("color:#8B92A0; font-size:11px;")
            h.addWidget(tag, alignment=Qt.AlignTop)
        return row

    def _next_scan_text(self) -> str:
        """스케줄에서 다음 자동 점검 시각 텍스트(정본: 6/9(월) 09:00)."""
        sch = getattr(self.cfg, "schedule", None) if self.cfg else None
        if not sch or not getattr(sch, "enabled", False):
            return "사용 안 함"
        from datetime import datetime, timedelta
        now = datetime.now()
        h, m = getattr(sch, "hour", 9), getattr(sch, "minute", 0)
        wd_ko = "월화수목금토일"
        freq = getattr(sch, "frequency", "weekly")
        if freq == "daily":
            nxt = now.replace(hour=h, minute=m, second=0, microsecond=0)
            if nxt <= now:
                nxt += timedelta(days=1)
        elif freq == "monthly":
            dom = getattr(sch, "day_of_month", 1)
            month, year = now.month, now.year
            try:
                nxt = now.replace(day=dom, hour=h, minute=m, second=0, microsecond=0)
            except ValueError:
                nxt = now
            if nxt <= now:
                month = month % 12 + 1
                year += 1 if month == 1 else 0
                nxt = nxt.replace(year=year, month=month)
        else:  # weekly
            target = {"mon": 0, "tue": 1, "wed": 2, "thu": 3,
                      "fri": 4, "sat": 5, "sun": 6}.get(getattr(sch, "day_of_week", "mon"), 0)
            days = (target - now.weekday()) % 7
            nxt = (now + timedelta(days=days)).replace(hour=h, minute=m, second=0, microsecond=0)
            if nxt <= now:
                nxt += timedelta(days=7)
        return f"{nxt.month}/{nxt.day}({wd_ko[nxt.weekday()]}) {h:02d}:{m:02d}"

    def _refresh_dashboard(self):
        """config.last_scan + 스케줄 + 격리 수로 대시보드를 채운다(시작 시/점검 후)."""
        if not hasattr(self, "dash_sub"):
            return
        self.stat_role._value_label.setText(", ".join(self.profiles))
        self.stat_next._value_label.setText(self._next_scan_text())
        try:
            from . import actions
            qn = (len(list(actions.QUARANTINE_DIR.glob("*.meta.json")))
                  if actions.QUARANTINE_DIR.exists() else 0)
        except Exception:
            qn = 0
        self.stat_quar._value_label.setText(f"{qn}개")

        ls = (getattr(self.cfg, "last_scan", None) or {}) if self.cfg else {}
        if not ls:
            return  # 점검 전 빈 상태 유지
        scanned = ls.get("scanned", 0)
        total = ls.get("total", 0)
        skipped = ls.get("skipped", 0)
        bysev = ls.get("bysev", {}) or {}
        grade = ls.get("grade", "안전")
        prev = ls.get("prev_total")
        self.dash_sub.setText(
            f"마지막 점검 {self._rel_time(ls.get('at',''))} · {scanned:,}개 파일 검사")
        for hw in (self.donut, self.shield_hero, self.numeric_hero):
            hw.set_data(bysev, grade)
        if total == 0 and skipped > 0:
            self.grade_chip_label.setText("확인 필요")
            self._style_sev_label(self.grade_chip_label, "중간")
            self.grade_label.setText(
                f"위험은 발견되지 않았지만 {skipped}개 파일을 검사하지 못했습니다(파서/OCR 미설치 등).")
        else:
            self._style_sev_label(
                self.grade_chip_label,
                {"위험": "높음", "주의": "중간", "안전": "낮음"}.get(grade, "낮음"))
            self.grade_chip_label.setText(f"● {grade}")  # 칩은 등급(위험/주의/안전) 표기
            if total:
                self.grade_label.setText(
                    f"주의가 필요한 항목 {total}건을 발견했어요. "
                    + {"위험": "즉시 조치가 필요해요.", "주의": "주의가 필요해요."}.get(grade, ""))
            else:
                self.grade_label.setText("점검한 파일에서 위험을 찾지 못했습니다. 안전합니다.")
        if prev is not None and prev != total:
            self.dash_prev.setText(f"지난 점검 {prev}건 → {total}건")
            self.dash_prev.setVisible(True)
        else:
            self.dash_prev.setVisible(False)
        self._prev_total = total

    # -------------------------------------------------------- 스캔 진행
    def _build_scanning(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(36, 28, 36, 28)
        lay.setSpacing(16)
        self._scan_log = []

        # 헤더: 제목/부제(좌) + 연출 세그먼트(우)
        head = QHBoxLayout()
        tcol = QVBoxLayout(); tcol.setSpacing(3)
        trow = QHBoxLayout(); trow.setSpacing(8)
        ti = QLabel(); ti.setFixedSize(24, 24)
        ti.setPixmap(icons.line_icon("search", 24, BRAND["brand"], 2.2))
        trow.addWidget(ti); trow.addWidget(_h1("스캔 진행 중")); trow.addStretch()
        tcol.addLayout(trow)
        self.scan_sub = QLabel("준비 중…")
        self.scan_sub.setStyleSheet("color:#565E6C; font-size:13px;")
        tcol.addWidget(self.scan_sub)
        head.addLayout(tcol); head.addStretch()
        seglbl = QLabel("연출")
        seglbl.setStyleSheet("color:#8B92A0; font-size:12px;")
        head.addWidget(seglbl, alignment=Qt.AlignBottom)
        head.addSpacing(4)
        scont, self._scan_seg = _make_segment(
            [("linear", "막대형", "list"), ("radial", "원형", "refresh"),
             ("minimal", "미니멀", "bolt")], self._set_scan_style)
        head.addWidget(scont, 0, Qt.AlignBottom)
        lay.addLayout(head)

        # 연출 스택
        self.scan_stack = QStackedWidget()
        self.scan_stack.addWidget(self._scan_page_linear())
        self.scan_stack.addWidget(self._scan_page_radial())
        self.scan_stack.addWidget(self._scan_page_minimal())
        lay.addWidget(self.scan_stack)

        # 실시간 검출 버킷(공유)
        bgrid = QHBoxLayout()
        bgrid.setSpacing(12)
        self._bucket_labels = {}
        for key, color in [("주민등록번호", "#B0123F"), ("신용카드번호", "#B0123F"),
                           ("API키/DB", "#E08600"), ("전화·이메일", "#2563EB")]:
            bc = _card()
            bcl = QVBoxLayout(bc)
            bcl.setContentsMargins(16, 12, 16, 12)
            t = QLabel(key)
            t.setStyleSheet("color:#565E6C; font-size:12px; font-weight:600;")
            bcl.addWidget(t)
            v = QLabel("0")
            v.setStyleSheet("font-size:26px; font-weight:800; color:#8B92A0;")
            v.setProperty("color", color)
            self._bucket_labels[key] = v
            bcl.addWidget(v)
            bgrid.addWidget(bc, 1)
        lay.addLayout(bgrid)

        self.ocr_note = QLabel("이미지 분석 중 — 시간이 조금 걸릴 수 있어요")
        self.ocr_note.setAlignment(Qt.AlignCenter)
        self.ocr_note.setStyleSheet("color:#E08600; font-size:12.5px; font-weight:600;")
        self.ocr_note.setVisible(False)
        lay.addWidget(self.ocr_note)

        lay.addStretch()
        btnrow = QHBoxLayout(); btnrow.addStretch()
        self.pause_btn = QPushButton("  일시정지")
        self.pause_btn.setObjectName("Ghost")
        self.pause_btn.setIcon(QIcon(icons.line_icon("pause", 15, "#565E6C")))
        self.pause_btn.setCursor(Qt.PointingHandCursor)
        self.pause_btn.clicked.connect(self._toggle_pause)
        btnrow.addWidget(self.pause_btn)
        cancel = QPushButton("  중지하고 결과 보기")
        cancel.setObjectName("Ghost")
        cancel.setIcon(QIcon(icons.line_icon("stop", 15, "#565E6C")))
        cancel.clicked.connect(self._cancel_scan)
        btnrow.addWidget(cancel)
        btnrow.addStretch()
        lay.addLayout(btnrow)

        self._set_scan_style("linear")
        return w

    def _scan_page_linear(self) -> QWidget:
        card = _card()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(22, 18, 22, 18)
        cl.setSpacing(14)
        stage_row = QHBoxLayout(); stage_row.setSpacing(10)
        self._stage_labels = []
        for icn, name in [("folder", "파일 수집"), ("search", "내용 검사"), ("cpu", "검증·분석")]:
            fr = QFrame(); fr.setObjectName("StageCard")
            fr.setStyleSheet("QFrame#StageCard{background:#F7F8FA;border:1px solid #E7E9EE;border-radius:10px;}")
            h = QHBoxLayout(fr); h.setContentsMargins(12, 10, 12, 10); h.setSpacing(9)
            box = QLabel(); box.setFixedSize(26, 26); box.setAlignment(Qt.AlignCenter)
            box.setStyleSheet("background:#E7E9EE; border-radius:7px;")
            box.setPixmap(icons.line_icon(icn, 15, "#8B92A0"))
            tl = QLabel(name); tl.setStyleSheet("font-weight:700; color:#8B92A0; font-size:13px;")
            h.addWidget(box); h.addWidget(tl); h.addStretch()
            self._stage_labels.append((fr, box, tl, icn))
            stage_row.addWidget(fr, 1)
        cl.addLayout(stage_row)
        pr = QHBoxLayout()
        pr.addWidget(QLabel("진행률")); pr.addStretch()
        self.pct_label = QLabel("0%")
        self.pct_label.setStyleSheet("font-size:26px; font-weight:800; color:#B0123F;")
        pr.addWidget(self.pct_label)
        cl.addLayout(pr)
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False); self.progress_bar.setFixedHeight(14)
        cl.addWidget(self.progress_bar)
        self.progress_path = QLabel("준비 중...")
        self.progress_path.setStyleSheet("color:#8B92A0; font-family:'JetBrains Mono',monospace; font-size:11.5px;")
        cl.addWidget(self.progress_path)
        return card

    def _scan_page_radial(self) -> QWidget:
        card = _card()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(22, 14, 22, 16)
        self.scan_ring = _ScanRing()
        cl.addWidget(self.scan_ring, 1)
        self.radial_path = QLabel("준비 중...")
        self.radial_path.setAlignment(Qt.AlignCenter)
        self.radial_path.setStyleSheet("color:#8B92A0; font-family:'JetBrains Mono',monospace; font-size:11.5px;")
        cl.addWidget(self.radial_path)
        return card

    def _scan_page_minimal(self) -> QWidget:
        card = _card()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(26, 20, 26, 20)
        cl.setSpacing(10)
        top = QHBoxLayout(); top.setAlignment(Qt.AlignBottom)
        self.min_pct = QLabel("0%")
        self.min_pct.setStyleSheet("font-size:82px; font-weight:800; color:#14161C;"
                                   "font-family:'JetBrains Mono','D2Coding',monospace; letter-spacing:-2px;")
        top.addWidget(self.min_pct, 0, Qt.AlignBottom); top.addStretch()
        fcol = QVBoxLayout(); fcol.setSpacing(0)
        self.min_found = QLabel("발견 0건")
        self.min_found.setStyleSheet("font-size:15px; font-weight:800; color:#B0123F;")
        self.min_found.setAlignment(Qt.AlignRight)
        fcol.addWidget(self.min_found)
        fl = QLabel("실시간 검출"); fl.setStyleSheet("color:#8B92A0; font-size:12px;")
        fl.setAlignment(Qt.AlignRight)
        fcol.addWidget(fl)
        top.addLayout(fcol)
        cl.addLayout(top)
        self.min_bar = QProgressBar()
        self.min_bar.setTextVisible(False); self.min_bar.setFixedHeight(4)
        cl.addWidget(self.min_bar)
        cl.addSpacing(6)
        self.min_log = QLabel("")
        self.min_log.setTextFormat(Qt.RichText)
        self.min_log.setStyleSheet(
            "background:#14161C; border-radius:12px; padding:16px 18px;"
            "font-family:'JetBrains Mono','D2Coding',monospace; font-size:12.5px;")
        self.min_log.setAlignment(Qt.AlignBottom | Qt.AlignLeft)
        self.min_log.setMinimumHeight(180)
        cl.addWidget(self.min_log, 1)
        return card

    def _set_scan_style(self, key: str):
        idx = {"linear": 0, "radial": 1, "minimal": 2}[key]
        self.scan_stack.setCurrentIndex(idx)
        _style_segment(self._scan_seg, key)

    def _toggle_pause(self):
        if not self.worker:
            return
        paused = self.worker.toggle_pause()
        self.pause_btn.setText("  재개" if paused else "  일시정지")
        self.pause_btn.setIcon(QIcon(icons.line_icon(
            "search" if paused else "pause", 15, "#565E6C")))

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
        # 뷰 세그먼트
        vcont, self._view_seg = _make_segment(
            [("table", "테이블", "list"), ("group", "그룹", "layers"),
             ("cards", "카드", "grid")], self._set_result_view)
        head.addWidget(vcont)
        head.addSpacing(12)
        self.report_btn = QPushButton("  완료 · 리포트")
        self.report_btn.setObjectName("Primary")
        self.report_btn.setIcon(QIcon(icons.line_icon("checkCircle", 16, "#fff")))
        self.report_btn.setCursor(Qt.PointingHandCursor)
        self.report_btn.clicked.connect(self._go_complete)
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

        self.result_views = QStackedWidget()
        self.result_views.addWidget(self._build_table_view())
        self.result_views.addWidget(self._build_group_view())
        self.result_views.addWidget(self._build_cards_view())
        lay.addWidget(self.result_views, 1)
        self._set_result_view("table")
        return w

    def _build_table_view(self) -> QWidget:
        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(12)

        # 가로 필터 행(정본 08)
        frow = QHBoxLayout(); frow.setSpacing(8)
        flab = QLabel("위험도")
        flab.setStyleSheet("color:#565E6C; font-size:12.5px; font-weight:700;")
        frow.addWidget(flab)
        self._sev_buttons = {}
        for key in ["전체", "높음", "중간", "낮음"]:
            b = QPushButton(key); b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, k=key: self._set_sev_filter(k))
            self._sev_buttons[key] = b
            frow.addWidget(b)
        frow.addStretch()
        fil = QLabel(); fil.setPixmap(icons.line_icon("list", 16, "#8B92A0", 2))
        frow.addWidget(fil)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("전체 파일")
        self.search_box.setFixedWidth(220)
        self.search_box.textChanged.connect(self._apply_filter)
        frow.addWidget(self.search_box)
        self.tbl_count = QLabel("0건")
        self.tbl_count.setStyleSheet("color:#8B92A0; font-size:12px; font-weight:600;")
        frow.addWidget(self.tbl_count)
        outer.addLayout(frow)

        # 마스킹 미리보기 — 목록 위쪽 가로형 패널(행 선택 시 표시).
        # 우측 고정 패널을 없애 목록이 전체 폭을 쓰도록 한다.
        from PySide6.QtWidgets import QSizePolicy
        self.preview = _card()
        self.preview.setVisible(False)
        self.preview.setFixedHeight(124)  # 세 블록 높이 균형용 고정 높이
        pv = QHBoxLayout(self.preview)
        pv.setContentsMargins(16, 12, 16, 14)
        pv.setSpacing(16)
        infow = QWidget(); infow.setFixedWidth(300)
        info = QVBoxLayout(infow); info.setContentsMargins(0, 0, 0, 0); info.setSpacing(3)
        info.addWidget(self._mini_label("마스킹 미리보기"))
        self.pv_file = QLabel(""); self.pv_file.setWordWrap(True)
        self.pv_file.setStyleSheet("font-weight:700; font-size:13.5px;")
        info.addWidget(self.pv_file)
        self.pv_path = QLabel("")  # 긴 경로는 한 줄 가운데 말줄임(_show_preview에서 처리)
        self.pv_path.setStyleSheet("color:#8B92A0; font-size:11.5px;")
        info.addWidget(self.pv_path)
        self.pv_type = QLabel("")
        info.addWidget(self.pv_type)
        info.addStretch()
        pv.addWidget(infow)
        self.pv_value = QLabel("")
        self.pv_value.setFixedWidth(200)
        self.pv_value.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.pv_value.setAlignment(Qt.AlignCenter)
        self.pv_value.setWordWrap(True)
        self.pv_value.setStyleSheet(
            "font-family:'JetBrains Mono','D2Coding',monospace; font-size:15px;"
            " background:#F7F8FA; border:1px solid #E7E9EE; border-radius:10px; padding:8px 12px;")
        pv.addWidget(self.pv_value)
        ctxw = QWidget()
        cvb = QVBoxLayout(ctxw); cvb.setContentsMargins(0, 0, 0, 0); cvb.setSpacing(6)
        ctxlbl = QLabel("검출 위치 (마스킹됨)")
        ctxlbl.setStyleSheet("color:#8B92A0; font-size:11.5px;")
        cvb.addWidget(ctxlbl)
        self.pv_ctx = QLabel(""); self.pv_ctx.setWordWrap(True)
        self.pv_ctx.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.pv_ctx.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.pv_ctx.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.pv_ctx.setStyleSheet(
            "font-family:'JetBrains Mono',monospace; font-size:11.5px; color:#CBD3E1;"
            " background:#1B1E25; border-radius:10px; padding:10px 12px; line-height:1.4;")
        cvb.addWidget(self.pv_ctx, 1)
        pv.addWidget(ctxw, 1)
        outer.addWidget(self.preview)

        # 행 리스트 카드(전체 폭 사용)
        listcard = _card()
        lc = QVBoxLayout(listcard); lc.setContentsMargins(8, 10, 8, 8); lc.setSpacing(0)
        hdr = QHBoxLayout(); hdr.setContentsMargins(12, 2, 12, 8); hdr.setSpacing(10)
        self.tbl_all = QCheckBox(); self.tbl_all.stateChanged.connect(self._toggle_all_rows)
        hdr.addWidget(self.tbl_all)
        for txt, w_ in [("위험도", 56), ("파일 · 검출 항목", 0)]:
            hl = QLabel(txt); hl.setStyleSheet("color:#8B92A0; font-size:11.5px; font-weight:700;")
            if w_:
                hl.setFixedWidth(w_)
            hdr.addWidget(hl)
        hdr.addStretch()
        hr = QLabel("조치"); hr.setStyleSheet("color:#8B92A0; font-size:11.5px; font-weight:700;")
        hdr.addWidget(hr)
        lc.addLayout(hdr)
        sc = QScrollArea(); sc.setWidgetResizable(True); sc.setFrameShape(QFrame.NoFrame)
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        host = QWidget(); self.tbl_list = QVBoxLayout(host)
        self.tbl_list.setContentsMargins(0, 0, 0, 0); self.tbl_list.setSpacing(4)
        self.tbl_list.addStretch()
        sc.setWidget(host); lc.addWidget(sc, 1)
        outer.addWidget(listcard, 1)

        # 하단 배치 조치 바
        bar = QHBoxLayout(); bar.setSpacing(10)
        for label, slot, obj, icn in [
                ("선택 마스킹", self._action_mask, "Ghost", "eyeOff"),
                ("선택 격리", self._action_quarantine, "Ghost", "lock"),
                ("이건 오탐이에요", self._mark_false_positive, "Ghost", "check"),
                ("완전삭제", self._action_delete, "Danger", "trash")]:
            b = QPushButton("  " + label); b.setObjectName(obj)
            b.setIcon(QIcon(icons.line_icon(icn, 15, "#fff" if obj == "Danger" else "#565E6C")))
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(slot)
            bar.addWidget(b)
        bar.addStretch()
        outer.addLayout(bar)
        return w

    def _table_row(self, path, finding):
        row = QFrame(); row.setObjectName("TRow")
        row.setStyleSheet(
            "QFrame#TRow{border-radius:9px;border:1px solid transparent;}"
            "QFrame#TRow:hover{background:#F7F8FA;}")
        h = QHBoxLayout(row); h.setContentsMargins(10, 8, 8, 8); h.setSpacing(8)
        chk = QCheckBox(); h.addWidget(chk)
        chip = QLabel(); self._style_sev_label(chip, finding.severity.value)
        chip.setFixedWidth(52); chip.setAlignment(Qt.AlignCenter)
        h.addWidget(chip)
        fic = QLabel(); fic.setFixedSize(17, 17)
        fic.setPixmap(icons.line_icon(_TYPE_ICON.get(finding.info_type, "fileText"), 16, "#565E6C", 2))
        h.addWidget(fic)
        desc = _type_desc(finding.info_type)
        col = QVBoxLayout(); col.setSpacing(2)
        t1row = QHBoxLayout(); t1row.setSpacing(6)
        t1 = QLabel(finding.info_type); t1.setStyleSheet("font-weight:700; font-size:13px;")
        t1.setToolTip(desc)
        t1row.addWidget(t1)
        if finding.field:  # 구조화 포맷(표/JSON)에서 검출 — 출처 열 라벨
            fld = QLabel(finding.field)
            fld.setStyleSheet(
                "background:#FCEFF3; color:#B0123F; border-radius:3px;"
                "padding:0 6px; font-size:10.5px; font-weight:700;")
            from PySide6.QtWidgets import QSizePolicy
            fld.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
            t1row.addWidget(fld)
        t1row.addStretch()
        col.addLayout(t1row)
        # 평이한 설명(무엇인지·왜 위험한지) — 한눈에 이해되도록 한 줄 노출.
        # Ignored 가로 정책: 라벨이 가로 폭을 강제하지 않아 행 전체가 넓어져
        # 조치 아이콘이 잘리는 것을 막는다(남는 폭에서 자동 말줄임).
        from PySide6.QtWidgets import QSizePolicy
        tdesc = QLabel(desc)
        tdesc.setStyleSheet("color:#7A828F; font-size:11px;")
        tdesc.setWordWrap(False)
        tdesc.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        tdesc.setToolTip(desc)
        col.addWidget(tdesc)
        src = f"{path.name} · line {finding.line}"
        if finding.field:
            src += f" · 열 “{finding.field}”"
        t2 = QLabel(src)
        t2.setStyleSheet("color:#A6ACB8; font-size:10.5px;")
        col.addWidget(t2)
        h.addLayout(col, 1)
        from PySide6.QtGui import QFontMetrics
        mv = QLabel()
        mv.setStyleSheet("font-family:'JetBrains Mono','D2Coding',monospace; font-size:11.5px; color:#565E6C;"
                         " background:#F7F8FA; border:1px solid #EEF0F3; border-radius:6px; padding:3px 6px;")
        mv.setFixedWidth(108)
        mv.setText(QFontMetrics(mv.font()).elidedText(finding.masked, Qt.ElideRight, 92))
        mv.setToolTip(finding.masked)
        mv.setAlignment(Qt.AlignCenter)
        h.addWidget(mv)
        h.addWidget(self._icon_btn("search", "파일 열기 (해당 위치)", lambda _=False, p=path, f=finding: self._open_finding(p, f.line)))
        h.addWidget(self._icon_btn("folder", "탐색기에서 위치 열기", lambda _=False, p=path: self._reveal_file(p)))
        h.addWidget(self._icon_btn("eyeOff", "마스킹", lambda _=False, p=path, f=finding: self._do_action("mask", p, [f])))
        h.addWidget(self._icon_btn("lock", "격리", lambda _=False, p=path, f=finding: self._do_action("quarantine", p, [f])))
        h.addWidget(self._icon_btn("trash", "삭제", lambda _=False, p=path, f=finding: self._do_action("delete", p, [f])))
        row.mousePressEvent = lambda e, p=path, f=finding: self._show_preview(p, f)
        return row, chk

    def _toggle_all_rows(self, state):
        checked = state == Qt.Checked.value if hasattr(Qt.Checked, "value") else bool(state)
        for r in getattr(self, "tbl_rows", []):
            if r["w"].isVisible():
                r["chk"].setChecked(checked)

    def _build_group_view(self) -> QWidget:
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        self.group_box = QVBoxLayout(inner)
        self.group_box.setContentsMargins(0, 0, 0, 0)
        self.group_box.setSpacing(12)
        self.group_box.addStretch()
        sc.setWidget(inner)
        return sc

    def _build_cards_view(self) -> QWidget:
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        self.cards_cols = QHBoxLayout(inner)
        self.cards_cols.setContentsMargins(0, 0, 0, 0)
        self.cards_cols.setSpacing(14)
        self._cards_col_box = {}
        for sev in ("높음", "중간", "낮음"):
            colw = QVBoxLayout()
            colw.setSpacing(10)
            head = QLabel()
            self._style_sev_label(head, sev)
            colw.addWidget(head)
            box = QVBoxLayout()
            box.setSpacing(10)
            colw.addLayout(box)
            colw.addStretch()
            self._cards_col_box[sev] = box
            cont = QWidget()
            cont.setLayout(colw)
            self.cards_cols.addWidget(cont, 1)
        sc.setWidget(inner)
        return sc

    def _set_result_view(self, key: str):
        idx = {"table": 0, "group": 1, "cards": 2}[key]
        self.result_views.setCurrentIndex(idx)
        _style_segment(self._view_seg, key)

    def _mini_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size:12px; font-weight:700; color:#565E6C;")
        return lbl

    def _set_sev_filter(self, key: str):
        palette = {"전체": "#565E6C", "높음": "#B0123F", "중간": "#E08600", "낮음": "#15A34A"}
        for k, b in self._sev_buttons.items():
            on = k == key
            b.setChecked(on)
            if on:
                b.setStyleSheet(
                    f"QPushButton{{border:1px solid {BRAND['brand']};border-radius:8px;"
                    f"padding:5px 12px;background:{BRAND['pink50']};color:{BRAND['brand']};"
                    "font-weight:700;font-size:12px;}")
            else:
                b.setStyleSheet(
                    f"QPushButton{{border:1px solid #E7E9EE;border-radius:8px;padding:5px 12px;"
                    f"background:#fff;color:{palette[k]};font-weight:700;font-size:12px;}}"
                    "QPushButton:hover{background:#F7F8FA;}")
        self._apply_filter()

    # -------------------------------------------------------- 완료
    def _build_complete(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(36, 28, 36, 28)
        lay.setSpacing(12)
        lay.addStretch()
        badge = QLabel()
        badge.setFixedSize(84, 84)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet("background:#E7F6EC; border-radius:42px;")
        badge.setPixmap(icons.line_icon("checkCircle", 46, "#15A34A", 2))
        h = QHBoxLayout(); h.addStretch(); h.addWidget(badge); h.addStretch()
        lay.addLayout(h)
        t = QLabel("점검 완료")
        t.setAlignment(Qt.AlignCenter)
        t.setStyleSheet("font-size:24px; font-weight:800;")
        lay.addWidget(t)
        s = QLabel("점검을 마쳤어요.")
        s.setAlignment(Qt.AlignCenter)
        s.setStyleSheet("color:#565E6C; font-size:13px;")
        lay.addWidget(s)

        stats = QHBoxLayout()
        stats.setSpacing(14)
        self._complete_stats = {}
        tiles = [("mask", "마스킹", "eyeOff", "#2563EB", "#EAF1FE"),
                 ("quarantine", "격리", "lock", BRAND["brand"], BRAND["pink50"]),
                 ("delete", "완전삭제", "trash", "#B0123F", "#FDEAEA")]
        for key, label, icn, color, bg in tiles:
            c = _card()
            cv = QVBoxLayout(c)
            cv.setContentsMargins(20, 18, 20, 18)
            cv.setSpacing(4)
            cv.setAlignment(Qt.AlignCenter)
            ibox = QLabel(); ibox.setFixedSize(38, 38); ibox.setAlignment(Qt.AlignCenter)
            ibox.setStyleSheet(f"background:{bg}; border-radius:10px;")
            ibox.setPixmap(icons.line_icon(icn, 19, color, 2))
            ih = QHBoxLayout(); ih.addStretch(); ih.addWidget(ibox); ih.addStretch()
            cv.addLayout(ih)
            num = QLabel("0")
            num.setAlignment(Qt.AlignCenter)
            num.setStyleSheet("font-size:30px; font-weight:800; color:#8B92A0;"
                              "font-family:'JetBrains Mono','D2Coding',monospace;")
            cv.addWidget(num)
            lb = QLabel(label); lb.setAlignment(Qt.AlignCenter)
            lb.setStyleSheet("color:#565E6C; font-size:12.5px; font-weight:600;")
            cv.addWidget(lb)
            self._complete_stats[key] = (num, color)
            stats.addWidget(c, 1)
        lay.addLayout(stats)

        cmp = _card()
        cl = QHBoxLayout(cmp)
        cl.setContentsMargins(20, 14, 20, 14)
        cl.addStretch()
        b1 = QVBoxLayout()
        l1 = QLabel("점검 전"); l1.setAlignment(Qt.AlignCenter); l1.setStyleSheet("color:#8B92A0; font-size:11px;")
        b1.addWidget(l1)
        self.cmp_before = QLabel(); self.cmp_before.setAlignment(Qt.AlignCenter)
        b1.addWidget(self.cmp_before)
        cl.addLayout(b1)
        arr = QLabel("›"); arr.setStyleSheet("font-size:18px; color:#8B92A0; margin:0 16px;")
        cl.addWidget(arr)
        b2 = QVBoxLayout()
        l2 = QLabel("점검 후"); l2.setAlignment(Qt.AlignCenter); l2.setStyleSheet("color:#8B92A0; font-size:11px;")
        b2.addWidget(l2)
        self.cmp_after = QLabel(); self.cmp_after.setAlignment(Qt.AlignCenter)
        b2.addWidget(self.cmp_after)
        cl.addLayout(b2)
        cl.addStretch()
        lay.addWidget(cmp)

        foot = QHBoxLayout()
        foot.addStretch()
        rep = QPushButton("진단 리포트 저장(PDF)")
        rep.setObjectName("Primary")
        rep.clicked.connect(self.save_report)
        foot.addWidget(rep)
        home = QPushButton("홈으로")
        home.setObjectName("Ghost")
        home.clicked.connect(lambda: (self._nav_buttons["dashboard"].click()))
        foot.addWidget(home)
        foot.addStretch()
        lay.addLayout(foot)
        lay.addStretch()
        return w

    def _go_complete(self):
        for key, (lbl, color) in self._complete_stats.items():
            n = self._action_counts.get(key, 0)
            lbl.setText(str(n))
            lbl.setStyleSheet(
                f"font-size:30px; font-weight:800; color:{color if n else '#8B92A0'};"
                "font-family:'JetBrains Mono','D2Coding',monospace;")
        before = getattr(self, "_scan_grade", "안전")
        handled = sum(self._action_counts.values())
        # 점검 후 등급: 처리로 남은 위험이 줄면 등급 재계산(간단화: 모두 처리 시 안전)
        ls = (getattr(self.cfg, "last_scan", None) or {}) if self.cfg else {}
        remaining = max(0, ls.get("total", 0) - handled)
        after = before if remaining else "안전"
        gmap = {"위험": "높음", "주의": "중간", "안전": "낮음"}
        self._style_sev_label(self.cmp_before, gmap.get(before, "낮음"))
        self.cmp_before.setText(f"● {before}")
        self._style_sev_label(self.cmp_after, gmap.get(after, "낮음"))
        self.cmp_after.setText(f"● {after}")
        self.stack.setCurrentWidget(self.complete)

    # -------------------------------------------------------- 격리함
    def _build_quarantine(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(36, 28, 36, 28)
        lay.setSpacing(8)
        lay.addWidget(_h1("격리함"))
        d = QLabel("격리된 파일은 암호화되어 안전하게 보관됩니다. 언제든 원래 위치로 복원할 수 있어요.")
        d.setStyleSheet("color:#565E6C; font-size:13px;")
        lay.addWidget(d)
        lay.addSpacing(6)

        self.q_scroll = QScrollArea()
        self.q_scroll.setWidgetResizable(True)
        self.q_scroll.setFrameShape(QFrame.NoFrame)
        self.q_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        host = QWidget()
        self.q_list = QVBoxLayout(host)
        self.q_list.setContentsMargins(0, 0, 0, 0)
        self.q_list.setSpacing(10)
        self.q_list.addStretch()
        self.q_scroll.setWidget(host)
        lay.addWidget(self.q_scroll, 1)
        # 빈 상태(아이콘 + 안내) — 콘텐츠 영역 세로 중앙
        self.q_empty = self._empty_state(
            "lock", "격리된 파일이 없습니다", "점검 결과에서 위험 항목을 격리하면 여기에 보관됩니다")
        lay.addWidget(self.q_empty, 1)
        return w

    def _empty_state(self, icon: str, title: str, sub: str) -> QWidget:
        """아이콘 + 제목 + 부제를 세로 중앙에 배치한 빈 상태 위젯."""
        w = QWidget()
        v = QVBoxLayout(w); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(10)
        v.addStretch()
        box = QLabel(); box.setFixedSize(64, 64); box.setAlignment(Qt.AlignCenter)
        box.setStyleSheet("background:#F1F2F4; border-radius:18px;")
        box.setPixmap(icons.line_icon(icon, 30, "#B0B6C2", 1.8))
        bh = QHBoxLayout(); bh.addStretch(); bh.addWidget(box); bh.addStretch()
        v.addLayout(bh)
        t = QLabel(title); t.setAlignment(Qt.AlignCenter)
        t.setStyleSheet("font-weight:700; font-size:14px; color:#8B92A0;")
        v.addWidget(t)
        s = QLabel(sub); s.setAlignment(Qt.AlignCenter)
        s.setStyleSheet("color:#B0B6C2; font-size:12px;")
        v.addWidget(s)
        v.addStretch()
        return w

    def _refresh_quarantine(self):
        from . import actions
        # 기존 카드 제거(끝의 stretch는 유지)
        while self.q_list.count() > 1:
            it = self.q_list.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        qdir = actions.QUARANTINE_DIR
        metas = []
        if qdir.exists():
            for mf in sorted(qdir.glob("*.meta.json")):
                try:
                    metas.append(json.loads(mf.read_text(encoding="utf-8")))
                except (json.JSONDecodeError, OSError):
                    continue
        for i, meta in enumerate(metas):
            self.q_list.insertWidget(i, self._quarantine_card(meta))
        self.q_empty.setVisible(not metas)
        self.q_scroll.setVisible(bool(metas))
        # 사이드바 배지
        if hasattr(self, "_q_badge"):
            n = len(metas)
            self._q_badge.setText(str(n))
            self._q_badge.setVisible(n > 0)
            self._position_q_badge()

    def _quarantine_card(self, meta: dict) -> QFrame:
        from pathlib import Path as _P
        card = _card()
        h = QHBoxLayout(card)
        h.setContentsMargins(16, 13, 16, 13)
        h.setSpacing(13)
        # 잠금 아이콘 박스
        lk = QLabel(); lk.setFixedSize(44, 44); lk.setAlignment(Qt.AlignCenter)
        lk.setStyleSheet(f"background:{BRAND['pink50']}; border-radius:11px;")
        lk.setPixmap(icons.line_icon("lock", 22, BRAND["brand"], 2))
        h.addWidget(lk)
        # 파일명 + 경로
        path = meta.get("original_path", "")
        info = QVBoxLayout(); info.setSpacing(2)
        fn = QLabel(_P(path).name or path)
        fn.setStyleSheet("font-weight:800; font-size:13.5px;")
        info.addWidget(fn)
        pl = QLabel(path)
        pl.setStyleSheet("color:#8B92A0; font-size:11px;")
        info.addWidget(pl)
        h.addLayout(info, 1)
        # 유형 + 시간 (한 줄)
        typ = meta.get("info_type") or "기타"
        tm_s = self._rel_time(meta.get("quarantined_at", ""))
        meta_row = QHBoxLayout(); meta_row.setSpacing(6)
        it = QLabel(typ)
        it.setStyleSheet("font-size:12.5px; color:#14161C;")
        meta_row.addWidget(it)
        if tm_s:
            tm = QLabel("· " + tm_s)
            tm.setStyleSheet("color:#8B92A0; font-size:11px;")
            meta_row.addWidget(tm)
        h.addLayout(meta_row)
        # 심각도 칩 — 값이 있을 때만 표시(없으면 빈 회색 박스 방지)
        sev = meta.get("severity") or None
        if sev:
            chip = QLabel()
            self._style_sev_label(chip, sev)
            h.addWidget(chip)
        # 복원 버튼
        qid = meta.get("id", "")
        restore = QPushButton("  복원"); restore.setObjectName("Ghost")
        restore.setIcon(QIcon(icons.line_icon("refresh", 14, "#565E6C", 2.2)))
        restore.setCursor(Qt.PointingHandCursor)
        restore.clicked.connect(lambda _=False, q=qid: self._restore_one(q))
        h.addWidget(restore)
        # 삭제 아이콘
        dele = QPushButton(); dele.setObjectName("IconBtn")
        dele.setFixedSize(34, 34)
        dele.setIcon(QIcon(icons.line_icon("trash", 17, "#B0123F", 2)))
        dele.setCursor(Qt.PointingHandCursor)
        dele.setStyleSheet("QPushButton#IconBtn{background:transparent;border:1px solid #E7E9EE;"
                           "border-radius:9px;} QPushButton#IconBtn:hover{background:#FDEAEA;border-color:#F6C4C4;}")
        dele.clicked.connect(lambda _=False, q=qid: self._delete_quarantine(q))
        h.addWidget(dele)
        return card

    @staticmethod
    def _rel_time(iso: str) -> str:
        if not iso:
            return ""
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(iso)
            delta = datetime.now() - dt
            secs = delta.total_seconds()
            if secs < 60:
                return "방금"
            if secs < 3600:
                return f"{int(secs // 60)}분 전"
            if secs < 86400:
                return f"{int(secs // 3600)}시간 전"
            if secs < 86400 * 30:
                return f"{int(secs // 86400)}일 전"
            return dt.strftime("%m/%d %H:%M")
        except ValueError:
            return iso

    def _restore_one(self, qid: str):
        from .actions import restore_file
        if restore_file(qid).status == "success":
            self._toast("원래 위치로 복원했습니다")
        self._refresh_quarantine()

    def _delete_quarantine(self, qid: str):
        from . import actions
        for suffix in (".enc", ".meta.json"):
            p = actions.QUARANTINE_DIR / f"{qid}{suffix}"
            try:
                if p.exists():
                    p.unlink()
            except OSError:
                pass
        self._toast("격리함에서 삭제했습니다")
        self._refresh_quarantine()

    def _restore_selected(self):
        self._refresh_quarantine()

    # -------------------------------------------------------- 점검 이력
    def _build_history(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(36, 28, 36, 28)
        lay.setSpacing(8)
        # 헤더: 제목/부제(좌) + 필터 세그먼트 + 내보내기(우)
        head = QHBoxLayout()
        tcol = QVBoxLayout(); tcol.setSpacing(3)
        tcol.addWidget(_h1("점검 이력"))
        d = QLabel("모든 스캔·조치 내역이 감사 로그로 기록됩니다. 컴플라이언스 증빙의 근거가 됩니다.")
        d.setStyleSheet("color:#565E6C; font-size:13px;")
        tcol.addWidget(d)
        head.addLayout(tcol); head.addStretch()
        self._hist_filter = "all"
        seg_cont, self._hist_seg = _make_segment(
            [("all", "전체", "list"), ("scan", "스캔", "search"),
             ("action", "조치", "checkCircle")],
            self._set_hist_filter)
        head.addWidget(seg_cont, alignment=Qt.AlignVCenter)
        head.addSpacing(8)
        exp = QPushButton("  내보내기"); exp.setObjectName("Ghost")
        exp.setMinimumHeight(36)
        exp.setIcon(QIcon(icons.line_icon("fileText", 15, "#565E6C")))
        exp.setCursor(Qt.PointingHandCursor)
        exp.clicked.connect(self._export_audit)
        head.addWidget(exp, alignment=Qt.AlignVCenter)
        lay.addLayout(head)
        lay.addSpacing(6)

        self.h_scroll = QScrollArea(); self.h_scroll.setWidgetResizable(True)
        self.h_scroll.setFrameShape(QFrame.NoFrame)
        self.h_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        host = QWidget(); self.h_list = QVBoxLayout(host)
        self.h_list.setContentsMargins(0, 0, 0, 0); self.h_list.setSpacing(10)
        self.h_list.addStretch()
        self.h_scroll.setWidget(host)
        lay.addWidget(self.h_scroll, 1)
        self.h_empty = self._empty_state(
            "history", "기록된 점검 이력이 없습니다", "점검·조치를 실행하면 여기에 시간순으로 쌓입니다")
        lay.addWidget(self.h_empty, 1)
        self._set_hist_filter("all")
        return w

    def _set_hist_filter(self, key: str):
        self._hist_filter = key
        _style_segment(self._hist_seg, key)
        self._refresh_history()

    def _refresh_history(self):
        if not hasattr(self, "h_list"):
            return
        while self.h_list.count() > 1:
            it = self.h_list.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        flt = getattr(self, "_hist_filter", "all")
        from . import results_store
        items = []
        # 저장된 스캔(재열람 가능) — 결과 화면으로 다시 열 수 있다.
        for s in results_store.list_scans():
            items.append({"kind": "scan", "ts": s.get("at", ""), "scan": s})
        # 조치 내역(감사 로그). 스캔류는 위 저장 결과로 대체하므로 제외.
        for e in _read_audit_tail(500):
            if e.get("action") in ("scan", "closing", "figma_scan"):
                continue
            items.append({"kind": "action", "ts": e.get("ts", ""), "audit": e})
        items.sort(key=lambda d: d.get("ts", ""), reverse=True)
        shown = 0
        for it in items:
            kind = it["kind"]
            if flt != "all" and kind != flt:
                continue
            if kind == "scan":
                card = self._scan_history_card(it["scan"])
            else:
                e = it["audit"]
                action = e.get("action", "")
                icn, title, _k = _HIST_META.get(
                    action, ("fileText", _ACTION_KO.get(action, action), "action"))
                card = self._history_card(e, icn, title, "action")
            self.h_list.insertWidget(shown, card)
            shown += 1
        self.h_empty.setVisible(shown == 0)
        self.h_scroll.setVisible(shown > 0)

    def _scan_history_card(self, s: dict) -> QFrame:
        """저장된 스캔 카드 — 클릭/‘결과 보기’로 상세 결과를 다시 연다."""
        card = _card()
        h = QHBoxLayout(card); h.setContentsMargins(16, 12, 16, 12); h.setSpacing(13)
        box = QLabel(); box.setFixedSize(40, 40); box.setAlignment(Qt.AlignCenter)
        box.setStyleSheet(f"background:{BRAND['pink50']}; border-radius:10px;")
        box.setPixmap(icons.line_icon("search", 19, BRAND["brand"], 2))
        h.addWidget(box)
        col = QVBoxLayout(); col.setSpacing(2)
        t = QLabel("전체 스캔 실행"); t.setStyleSheet("font-weight:800; font-size:13.5px;")
        col.addWidget(t)
        bysev = s.get("bysev", {}) or {}
        sub = (f"{', '.join(s.get('profiles', []))} · {s.get('scanned', 0):,}개 검사"
               f" · 위험 {s.get('total', 0)}건  "
               f"(높음 {bysev.get('높음', 0)}·중간 {bysev.get('중간', 0)}·낮음 {bysev.get('낮음', 0)})")
        sl = QLabel(sub); sl.setStyleSheet("color:#8B92A0; font-size:11.5px;")
        col.addWidget(sl)
        h.addLayout(col, 1)
        grade = QLabel(s.get("grade", "안전"))
        self._style_sev_label(grade, {"위험": "높음", "주의": "중간", "안전": "낮음"}.get(
            s.get("grade", "안전")))
        h.addWidget(grade, alignment=Qt.AlignVCenter)
        sid = s.get("id")
        open_btn = QPushButton("  결과 보기"); open_btn.setObjectName("Ghost")
        open_btn.setIcon(QIcon(icons.line_icon("chevR", 14, "#565E6C")))
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.clicked.connect(lambda _=False, i=sid: self._open_saved_scan(i))
        h.addWidget(open_btn, alignment=Qt.AlignVCenter)
        ts = s.get("at", "")
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(ts)
            ts = f"{dt.month}/{dt.day} {dt.hour:02d}:{dt.minute:02d}"
        except (ValueError, TypeError):
            pass
        when = QLabel(ts); when.setStyleSheet("color:#8B92A0; font-size:11.5px;")
        h.addWidget(when, alignment=Qt.AlignTop)
        card.setCursor(Qt.PointingHandCursor)
        card.mousePressEvent = lambda e, i=sid: self._open_saved_scan(i)
        return card

    def _history_card(self, e: dict, icn: str, title: str, kind: str) -> QFrame:
        from pathlib import Path as _P
        card = _card()
        h = QHBoxLayout(card); h.setContentsMargins(16, 12, 16, 12); h.setSpacing(13)
        box = QLabel(); box.setFixedSize(40, 40); box.setAlignment(Qt.AlignCenter)
        tone = {"scan": (BRAND["pink50"], BRAND["brand"]),
                "action": ("#F1F2F4", "#565E6C")}[kind]
        box.setStyleSheet(f"background:{tone[0]}; border-radius:10px;")
        box.setPixmap(icons.line_icon(icn, 19, tone[1], 2))
        h.addWidget(box)
        col = QVBoxLayout(); col.setSpacing(2)
        t = QLabel(title); t.setStyleSheet("font-weight:800; font-size:13.5px;")
        col.addWidget(t)
        if kind == "scan":
            sub = (f"{e.get('profile','')} 프로파일 · {e.get('files',0):,}개 검사"
                   f" · 위험 {e.get('findings',0)}건")
        else:
            name = _P(e.get("path", "")).name or e.get("path", "")
            sub = f"{name} · {e.get('result','')}"
        sl = QLabel(sub); sl.setStyleSheet("color:#8B92A0; font-size:11.5px;")
        col.addWidget(sl)
        h.addLayout(col, 1)
        ts = e.get("ts", "")
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(ts)
            ts = f"{dt.month}/{dt.day} {dt.hour:02d}:{dt.minute:02d}"
        except (ValueError, TypeError):
            pass
        when = QLabel(ts)
        when.setStyleSheet("color:#8B92A0; font-size:11.5px;")
        h.addWidget(when, alignment=Qt.AlignTop)
        return card

    # -------------------------------------------------------- 설정
    def _build_settings(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(36, 28, 36, 28)
        lay.setSpacing(16)
        lay.addWidget(_h1("설정"))

        body = QHBoxLayout()
        body.setSpacing(18)
        # 좌측 탭 내비
        navc = QWidget()
        navc.setFixedWidth(190)
        nl = QVBoxLayout(navc)
        nl.setContentsMargins(0, 0, 0, 0)
        nl.setSpacing(2)
        self._settings_tabs = {}
        for key, label, ic in [("general", "일반", "settings"), ("scan", "스캔", "search"),
                               ("auto", "자동 점검", "clock"), ("security", "보안", "shield"),
                               ("whitelist", "오탐 제외", "eyeOff"),
                               ("about", "정보", "fileText")]:
            b = QPushButton("  " + label)
            b.setObjectName("Nav")
            b.setCheckable(True)
            b.setIcon(QIcon(icons.line_icon(ic, 17, "#565E6C")))
            b.setIconSize(QSize(17, 17))
            b.clicked.connect(lambda _=False, k=key: self._set_settings_tab(k))
            self._settings_tabs[key] = b
            nl.addWidget(b)
        nl.addStretch()
        body.addWidget(navc)

        self.settings_stack = QStackedWidget()
        self.settings_stack.addWidget(self._settings_general())
        self.settings_stack.addWidget(self._settings_scan())
        self.settings_stack.addWidget(self._settings_auto())
        self.settings_stack.addWidget(self._settings_security())
        self.settings_stack.addWidget(self._settings_whitelist())
        self.settings_stack.addWidget(self._settings_about())
        body.addWidget(self.settings_stack, 1)
        lay.addLayout(body, 1)
        self._set_settings_tab("general")
        return w

    def _settings_general(self) -> QWidget:
        c = _card()
        gl = QVBoxLayout(c)
        gl.setContentsMargins(24, 20, 24, 20)
        gl.setSpacing(14)
        # 직무 프로파일
        r1 = QHBoxLayout()
        col = QVBoxLayout(); col.setSpacing(1)
        t = QLabel("직무 프로파일"); t.setStyleSheet("font-weight:700; font-size:14px;")
        col.addWidget(t)
        d = QLabel("선택한 직무에 맞춰 스캔 폴더·검출 항목이 구성됩니다")
        d.setStyleSheet("color:#565E6C; font-size:12px;")
        col.addWidget(d)
        r1.addLayout(col); r1.addStretch()
        rolebtn = QPushButton("  " + (", ".join(self.profiles)) + "  ▾")
        rolebtn.setObjectName("Ghost")
        rolebtn.setIcon(QIcon(icons.line_icon(icons.ROLE_ICON.get(self.profiles[0], "user"), 15, "#B0123F")))
        rolebtn.clicked.connect(self._open_role_popover)
        self._settings_rolebtn = rolebtn
        r1.addWidget(rolebtn)
        gl.addLayout(r1)
        gl.addWidget(self._hline())
        # 테마
        r2 = QHBoxLayout()
        col2 = QVBoxLayout(); col2.setSpacing(1)
        t2 = QLabel("테마"); t2.setStyleSheet("font-weight:700; font-size:14px;")
        col2.addWidget(t2)
        d2 = QLabel("야간 작업이 많다면 다크 모드를 권장합니다")
        d2.setStyleSheet("color:#565E6C; font-size:12px;")
        col2.addWidget(d2)
        r2.addLayout(col2); r2.addStretch()
        self._theme_seg = {}
        tseg = QFrame(); tseg.setObjectName("Seg")
        tseg.setStyleSheet("QFrame#Seg{background:#EFF1F4; border:1px solid #E7E9EE; border-radius:9px;}")
        th = QHBoxLayout(tseg); th.setContentsMargins(3, 3, 3, 3); th.setSpacing(2)
        for key, label in [("light", "라이트"), ("dark", "다크")]:
            b = QPushButton(label); b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, k=key: self._set_theme(k))
            self._theme_seg[key] = b
            th.addWidget(b)
        r2.addWidget(tseg)
        gl.addLayout(r2)
        gl.addWidget(self._hline())
        # 언어
        r3 = QHBoxLayout()
        t3 = QLabel("언어"); t3.setStyleSheet("font-weight:700; font-size:14px;")
        r3.addWidget(t3); r3.addStretch()
        r3.addWidget(QLabel("한국어"))
        gl.addLayout(r3)
        gl.addStretch()
        self._set_theme(self.theme)
        return self._tab_wrap(c)

    def _settings_scan(self) -> QWidget:
        c = _card()
        gl = QVBoxLayout(c)
        gl.setContentsMargins(24, 20, 24, 20)
        gl.setSpacing(12)
        self.ocr_check = QCheckBox("이미지 속 신분증·계약서도 검사 (로컬 OCR)")
        self.ocr_check.setChecked(getattr(self.cfg, "ocr_mode", "local") != "off")
        gl.addWidget(self.ocr_check)
        gl.addWidget(self._hline())
        gl.addWidget(QLabel("지원 파일 형식"))
        ex = QLabel("txt · csv · log · 소스코드 · xlsx · xls · docx · hwp · hwpx · pdf · "
                    "이미지(OCR) · psd · xd")
        ex.setWordWrap(True); ex.setStyleSheet("color:#565E6C; font-size:12px;")
        gl.addWidget(ex)
        gl.addStretch()
        return self._tab_wrap(c)

    def _settings_auto(self) -> QWidget:
        c = _card()
        gl = QVBoxLayout(c)
        gl.setContentsMargins(24, 20, 24, 20)
        gl.setSpacing(12)
        fr = QHBoxLayout()
        fr.addWidget(QLabel("자동 점검 주기"))
        fr.addStretch()
        self.freq_box = QComboBox()
        self.freq_box.addItems(_FREQ_ITEMS)
        sc = getattr(self.cfg, "schedule", None)
        if sc and getattr(sc, "enabled", False):
            self.freq_box.setCurrentText({"daily": "매일", "weekly": "매주(월요일)",
                                          "monthly": "매월(1일)"}.get(sc.frequency, "매주(월요일)"))
        fr.addWidget(self.freq_box)
        gl.addLayout(fr)
        note = QLabel("정해진 주기에 백그라운드에서 자동으로 PC를 점검하고 리포트를 남깁니다.\n"
                      "자동 완전삭제는 제공하지 않습니다(사고 방지).")
        note.setStyleSheet("color:#565E6C; font-size:12px;")
        gl.addWidget(note)
        gl.addStretch()
        return self._tab_wrap(c)

    def _settings_security(self) -> QWidget:
        c = _card()
        gl = QVBoxLayout(c)
        gl.setContentsMargins(24, 20, 24, 20)
        gl.setSpacing(12)
        from . import actions
        qr = QHBoxLayout()
        qr.addWidget(QLabel("격리 폴더"))
        qr.addStretch()
        ql = QLabel(str(actions.QUARANTINE_DIR))
        ql.setStyleSheet("color:#565E6C; font-size:11.5px; font-family:'JetBrains Mono',monospace;")
        qr.addWidget(ql)
        gl.addLayout(qr)
        ar = QHBoxLayout()
        ar.addWidget(QLabel("감사 로그"))
        ar.addStretch()
        exp = QPushButton("CSV로 내보내기")
        exp.setObjectName("Ghost")
        exp.clicked.connect(self._export_audit)
        ar.addWidget(exp)
        gl.addLayout(ar)
        gl.addWidget(self._hline())
        try:
            from .ui.settings_figma import FigmaOptInSection
            self.figma_section = FigmaOptInSection()
            self.figma_section.scan_requested.connect(self.run_figma_scan)
            gl.addWidget(self.figma_section)
        except Exception:
            self.figma_section = None
        gl.addStretch()
        return self._tab_wrap(c)

    def _settings_about(self) -> QWidget:
        c = _card()
        gl = QVBoxLayout(c)
        gl.setContentsMargins(24, 20, 24, 20)
        gl.setSpacing(14)
        top = QHBoxLayout()
        logo = QLabel()
        logo.setFixedSize(52, 52)
        logo.setPixmap(icons.shield_pixmap(52, stroke=3, color="#FFFFFF", bg="#B0123F"))
        top.addWidget(logo)
        tc = QVBoxLayout(); tc.setSpacing(2)
        nm = QLabel('솔리가드 <span style="color:#B0123F;">SoliGuard</span>')
        nm.setStyleSheet("font-size:18px; font-weight:800;")
        tc.addWidget(nm)
        ver = QLabel("v" + getattr(__import__("soliguard"), "__version__", "1.0") + " · solideo")
        ver.setStyleSheet("color:#8B92A0; font-size:12px;")
        tc.addWidget(ver)
        top.addLayout(tc); top.addStretch()
        gl.addLayout(top)
        gl.addWidget(self._hline())
        p1 = QLabel("제품"); p1.setStyleSheet("font-weight:700;")
        gl.addWidget(p1)
        p2 = QLabel("SI 실무자를 위한 직무 맞춤형 개인정보 자가점검 도구")
        p2.setStyleSheet("color:#565E6C; font-size:12.5px;")
        gl.addWidget(p2)
        gl.addWidget(self._hline())
        ur = QHBoxLayout()
        uc = QVBoxLayout(); uc.setSpacing(1)
        u1 = QLabel("업데이트"); u1.setStyleSheet("font-weight:700;")
        uc.addWidget(u1)
        self._upd_status = QLabel(
            "현재 버전 v" + getattr(__import__("soliguard"), "__version__", "1.0"))
        self._upd_status.setStyleSheet("color:#565E6C; font-size:12px;")
        uc.addWidget(self._upd_status)
        ur.addLayout(uc); ur.addStretch()
        self._upd_btn = QPushButton("업데이트 확인")
        self._upd_btn.setObjectName("Ghost")
        self._upd_btn.setCursor(Qt.PointingHandCursor)
        self._upd_btn.clicked.connect(self._check_update)
        ur.addWidget(self._upd_btn)
        gl.addLayout(ur)
        gl.addStretch()
        return self._tab_wrap(c)

    def _settings_whitelist(self) -> QWidget:
        """오탐 제외(화이트리스트) 관리 — 조회/추가/삭제(즉시 저장)."""
        c = _card()
        gl = QVBoxLayout(c)
        gl.setContentsMargins(22, 20, 22, 20)
        gl.setSpacing(12)
        t = QLabel("오탐 제외 (화이트리스트)")
        t.setStyleSheet("font-size:15px; font-weight:800;")
        gl.addWidget(t)
        d = QLabel("여기에 등록한 값은 다음 점검부터 검출에서 제외됩니다. "
                   "검출 결과의 '이건 오탐이에요'로도 추가됩니다.")
        d.setWordWrap(True)
        d.setStyleSheet("color:#565E6C; font-size:12.5px;")
        gl.addWidget(d)

        addrow = QHBoxLayout(); addrow.setSpacing(8)
        self._wl_input = QLineEdit()
        self._wl_input.setPlaceholderText("제외할 값 입력 (예: 010-1234-5678)")
        self._wl_input.returnPressed.connect(self._wl_add)
        addrow.addWidget(self._wl_input, 1)
        addb = QPushButton("  추가"); addb.setObjectName("Ghost")
        addb.setIcon(QIcon(icons.line_icon("plus", 15, "#565E6C")))
        addb.setCursor(Qt.PointingHandCursor)
        addb.clicked.connect(self._wl_add)
        addrow.addWidget(addb)
        gl.addLayout(addrow)

        self._wl_scroll = QScrollArea(); self._wl_scroll.setWidgetResizable(True)
        self._wl_scroll.setFrameShape(QFrame.NoFrame)
        self._wl_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        host = QWidget(); self._wl_list = QVBoxLayout(host)
        self._wl_list.setContentsMargins(0, 0, 0, 0); self._wl_list.setSpacing(6)
        self._wl_list.addStretch()
        self._wl_scroll.setWidget(host)
        gl.addWidget(self._wl_scroll, 1)
        self._wl_empty = QLabel("등록된 제외 값이 없습니다.")
        self._wl_empty.setStyleSheet("color:#8B92A0; font-size:12px; padding:8px 2px;")
        gl.addWidget(self._wl_empty)
        self._wl_refresh()

        w = QWidget(); v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(c)
        return w

    def _wl_refresh(self):
        if not hasattr(self, "_wl_list"):
            return
        wl = list(getattr(self.cfg, "whitelist", []) or [])
        while self._wl_list.count() > 1:
            it = self._wl_list.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        for val in wl:
            row = QFrame(); row.setObjectName("WlRow")
            row.setStyleSheet("QFrame#WlRow{background:#F7F8FA;border:1px solid #E7E9EE;"
                              "border-radius:8px;}")
            rl = QHBoxLayout(row); rl.setContentsMargins(12, 7, 8, 7); rl.setSpacing(8)
            lab = QLabel(val); lab.setStyleSheet("font-size:12.5px;")
            rl.addWidget(lab, 1)
            rm = QPushButton(); rm.setObjectName("IconBtn"); rm.setFixedSize(28, 28)
            rm.setIcon(QIcon(icons.line_icon("trash", 15, "#B0123F")))
            rm.setCursor(Qt.PointingHandCursor)
            rm.setStyleSheet("QPushButton#IconBtn{background:transparent;border:none;"
                             "border-radius:7px;}QPushButton#IconBtn:hover{background:#FDEAEA;}")
            rm.clicked.connect(lambda _=False, v=val: self._wl_remove(v))
            rl.addWidget(rm)
            self._wl_list.insertWidget(self._wl_list.count() - 1, row)
        self._wl_empty.setVisible(not wl)
        self._wl_scroll.setVisible(bool(wl))

    def _wl_save(self, wl: list):
        from .config import AppConfig
        cfg = self.cfg or AppConfig.load()
        cfg.whitelist = wl
        cfg.save()
        self.cfg = cfg

    def _wl_add(self):
        val = self._wl_input.text().strip()
        if not val:
            return
        wl = list(getattr(self.cfg, "whitelist", []) or [])
        if val in wl:
            self._wl_input.clear()
            self._warn("중복", "이미 등록된 값입니다.")
            return
        wl.append(val)
        self._wl_save(wl)
        self._wl_input.clear()
        self._wl_refresh()
        self._toast("제외 목록에 추가했습니다.")

    def _wl_remove(self, val: str):
        wl = [x for x in (getattr(self.cfg, "whitelist", []) or []) if x != val]
        self._wl_save(wl)
        self._wl_refresh()
        self._toast("제외 목록에서 제거했습니다.")

    def _tab_wrap(self, card) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(card)
        bar = QHBoxLayout()
        bar.addStretch()
        save = QPushButton("설정 저장")
        save.setObjectName("Primary")
        save.clicked.connect(self._save_settings)
        bar.addWidget(save)
        v.addLayout(bar)
        v.addStretch()
        return w

    def _hline(self) -> QFrame:
        ln = QFrame(); ln.setFrameShape(QFrame.HLine)
        ln.setStyleSheet("color:#E7E9EE;")
        ln.setFixedHeight(1)
        return ln

    def _set_settings_tab(self, key: str):
        order = ["general", "scan", "auto", "security", "whitelist", "about"]
        self.settings_stack.setCurrentIndex(order.index(key))
        for k, b in self._settings_tabs.items():
            b.setChecked(k == key)

    def _set_theme(self, theme: str):
        self.theme = theme
        app = QApplication.instance()
        if app:
            app.setStyleSheet(build_qss(theme))
        for k, b in self._theme_seg.items():
            on = k == theme
            b.setChecked(on)
            b.setStyleSheet(_seg_btn_qss(on))

    def _export_audit(self):
        rows0 = _read_audit_tail(100000)
        if not rows0:
            self._notice("감사 로그", "아직 기록이 없습니다.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "감사 로그 내보내기", "audit.csv", "CSV (*.csv)")
        if not path:
            return
        import csv
        rows = rows0
        try:
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                wr = csv.writer(f)
                wr.writerow(["시각", "작업", "대상", "결과", "사용자"])
                for e in rows:
                    wr.writerow([e.get("ts", ""), _ACTION_KO.get(e.get("action", ""), e.get("action", "")),
                                 e.get("path", ""), e.get("result", ""), e.get("user", "")])
            self._success("감사 로그", f"내보냈습니다: {path}")
        except OSError as ex:
            self._warn("내보내기 실패", str(ex))

    def _save_settings(self):
        try:
            from .config import AppConfig, ScheduleConfig
            cfg = self.cfg or AppConfig.load()
            cfg.profiles = list(self.profiles)
            cfg.profile = self.profiles[0] if self.profiles else "개발자"
            cfg.ocr_mode = "local" if self.ocr_check.isChecked() else "off"
            cfg.theme = getattr(self, "theme", "light")
            enabled = self.freq_box.currentText() != "사용 안 함"
            freq = {"매일": "daily", "매주(월요일)": "weekly",
                    "매월(1일)": "monthly"}.get(self.freq_box.currentText(), "weekly")
            cfg.schedule = ScheduleConfig(enabled=enabled, frequency=freq)
            cfg.save()
            self.cfg = cfg
            self._success("설정", "설정을 저장했습니다.")
        except Exception as e:
            self._warn("설정 저장 실패", str(e))

    def _style_sev_label(self, lbl, sev):
        # 소프트 pill(테두리 없음). 가로 레이아웃에서 세로로 늘어나지 않도록
        # 크기 정책을 고정해 텍스트 높이에 딱 맞춘다.
        from PySide6.QtWidgets import QSizePolicy
        lbl.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        _css = ("border:none; border-radius:2px; padding:2px 9px;"
                " font-weight:700; font-size:11px;")
        if sev is None:
            lbl.setStyleSheet("background:#F1F2F4; color:#8B92A0;" + _css)
            return
        color, bg, _line = SEV_CHIP.get(sev, ("#8B92A0", "#F1F2F4", "#E7E9EE"))
        lbl.setText("● " + sev)
        lbl.setStyleSheet(f"background:{bg}; color:{color};" + _css)

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

        # 전체 스캔 범위 카드 (정본 04)
        scope = _card()
        scl = QHBoxLayout(scope)
        scl.setContentsMargins(20, 16, 20, 16)
        scl.setSpacing(14)
        self.sc_scope_icon = QLabel()
        self.sc_scope_icon.setFixedSize(48, 48)
        self.sc_scope_icon.setAlignment(Qt.AlignCenter)
        self.sc_scope_icon.setStyleSheet(
            f"background:{BRAND['brand']}; border-radius:12px;")
        self.sc_scope_icon.setPixmap(icons.line_icon("search", 24, "#FFFFFF", 2.2))
        scl.addWidget(self.sc_scope_icon)
        sct = QVBoxLayout(); sct.setSpacing(2)
        self.sc_scope_title = QLabel("전체 스캔")
        self.sc_scope_title.setStyleSheet("font-size:15px; font-weight:800;")
        sct.addWidget(self.sc_scope_title)
        self.sc_scope_desc = QLabel("지정한 폴더와 드라이브를 빠짐없이 검사합니다")
        self.sc_scope_desc.setStyleSheet("color:#565E6C; font-size:12.5px;")
        sct.addWidget(self.sc_scope_desc)
        scl.addLayout(sct, 1)
        lay.addWidget(scope)

        cols = QHBoxLayout()
        cols.setSpacing(18)
        # 폴더
        fcard = _card()
        fl = QVBoxLayout(fcard)
        fl.setContentsMargins(20, 16, 20, 16)
        fl.setSpacing(8)
        fh = QHBoxLayout(); fh.setSpacing(8)
        ft = QLabel("스캔 대상 폴더")
        ft.setStyleSheet("font-size:15px; font-weight:800;")
        fh.addWidget(ft)
        self.sc_folder_count = QLabel("")
        self.sc_folder_count.setStyleSheet("color:#8B92A0; font-size:12px; font-weight:600;")
        fh.addWidget(self.sc_folder_count)
        fh.addStretch()
        addf = QPushButton("  폴더 추가")
        addf.setObjectName("Ghost")
        addf.setIcon(QIcon(icons.line_icon("plus", 15, "#565E6C", 2.4)))
        addf.clicked.connect(self._add_scan_folder)
        fh.addWidget(addf)
        fl.addLayout(fh)
        self.sc_folder_box = QVBoxLayout()
        self.sc_folder_box.setSpacing(8)
        fl.addLayout(self.sc_folder_box)
        fl.addStretch()
        cols.addWidget(fcard, 1)
        # 검출 항목(직무 기반) — 크림슨 pill 칩
        kcard = _card()
        kl = QVBoxLayout(kcard)
        kl.setContentsMargins(20, 16, 20, 16)
        kl.setSpacing(4)
        kh = QHBoxLayout(); kh.setSpacing(8)
        kt = QLabel("검출할 항목")
        kt.setStyleSheet("font-size:15px; font-weight:800;")
        kh.addWidget(kt)
        self.sc_kind_count = QLabel("")
        self.sc_kind_count.setStyleSheet("color:#8B92A0; font-size:12px; font-weight:600;")
        kh.addWidget(self.sc_kind_count)
        kh.addStretch()
        kl.addLayout(kh)
        self.sc_kind_sub = QLabel("")
        self.sc_kind_sub.setStyleSheet("color:#8B92A0; font-size:12px;")
        kl.addWidget(self.sc_kind_sub)
        self.sc_kinds_grid = QGridLayout()
        self.sc_kinds_grid.setSpacing(8)
        self.sc_kinds_grid.setContentsMargins(0, 8, 0, 0)
        kl.addLayout(self.sc_kinds_grid)
        self.sc_kind_note = QLabel("")
        self.sc_kind_note.setWordWrap(True)
        self.sc_kind_note.setStyleSheet(f"color:{BRAND['brand']}; font-size:11.5px; font-weight:600; padding-top:10px;")
        kl.addWidget(self.sc_kind_note)
        self.sc_kind_formats = QLabel("")
        self.sc_kind_formats.setWordWrap(True)
        self.sc_kind_formats.setStyleSheet("color:#8B92A0; font-size:11.5px; padding-top:6px;")
        kl.addWidget(self.sc_kind_formats)
        kl.addStretch()
        cols.addWidget(kcard, 1)
        lay.addLayout(cols, 1)

        foot = QHBoxLayout()
        trust = QLabel("스캔은 이 PC 안에서만 수행되며, 검출된 데이터는 외부로 전송되지 않습니다.")
        trust.setStyleSheet("color:#8B92A0; font-size:12px;")
        foot.addWidget(trust)
        foot.addStretch()
        startb = QPushButton("스캔 시작")
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
        scope_meta = {
            "full": ("search", "전체 스캔", "지정한 폴더와 드라이브를 빠짐없이 검사합니다"),
            "quick": ("bolt", "빠른 점검", "위험 폴더만 빠르게 훑습니다"),
            "closing": ("archive", "프로젝트 클로징 점검",
                        "프로젝트 폴더의 잔여 발주처 데이터를 일괄 점검합니다"),
        }[scope]
        self.sc_scope_icon.setPixmap(icons.line_icon(scope_meta[0], 24, "#FFFFFF", 2.2))
        self.sc_scope_title.setText(scope_meta[1])
        self.sc_scope_desc.setText(scope_meta[2])
        self.sc_sub.setText(
            "검사할 폴더와 파일 형식을 확인하세요. 폴더는 자유롭게 추가할 수 있고, "
            "파일 형식은 직무 프로파일이 정합니다.")
        # 스캔 폴더 — 직무와 무관하게 사용자가 설정한 폴더(기본: 다운로드).
        from .profiles import default_folders
        folders = list(getattr(self.cfg, "target_folders", None) or []) or default_folders()
        self._sc_folders = []
        while self.sc_folder_box.count():
            it = self.sc_folder_box.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        for p in folders:
            self._add_folder_row(str(p), True)
        # 전체 드라이브 옵션(정본 04)
        self._add_folder_row("전체 드라이브 (C:\\)", False)
        self._refresh_folder_count()
        # 검출 항목(직무 기반) — 크림슨 pill 칩
        kinds = ["주민등록번호", "신용카드", "전화·이메일", "계좌번호", "사업자번호"]
        if "개발자" in self.profiles:
            kinds.append("DB·API키")
        ocr_on = bool(self.cfg and getattr(self.cfg, "ocr_mode", "local") != "off")
        self._fill_kind_chips(kinds, ocr_on)
        self.sc_kind_count.setText(f"{len(kinds) + (1 if ocr_on else 0)}개 항목")
        self.sc_kind_sub.setText(f"직무: {', '.join(self.profiles)} 기본값")
        # 직무 특화 설명 + 파일 형식(정본 04)
        if "개발자" in self.profiles:
            self.sc_kind_note.setText("개발자 특화 — 소스코드·설정파일의 시크릿을 엔트로피로 검증합니다")
            self.sc_kind_note.setVisible(True)
        else:
            self.sc_kind_note.setVisible(False)
        from .profiles import PROFILE_EXTENSIONS
        exts = set()
        for role in self.profiles:
            exts |= PROFILE_EXTENSIONS.get(role, set())
        if exts:
            fmt = ", ".join(sorted(e.lstrip(".") for e in exts))
            self.sc_kind_formats.setText(f"파일 형식: {fmt}")
            self.sc_kind_formats.setVisible(True)
        else:
            self.sc_kind_formats.setVisible(False)
        self._select_nav("dashboard")
        self.stack.setCurrentWidget(self.scanconfig)

    def _fill_kind_chips(self, kinds, ocr_on):
        while self.sc_kinds_grid.count():
            it = self.sc_kinds_grid.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        items = [(k, True) for k in kinds]
        items.append(("이미지 속 정보(OCR)", ocr_on))
        items.append(("한글(HWP) 문서", True))
        self.sc_kinds_grid.setColumnStretch(0, 1)
        self.sc_kinds_grid.setColumnStretch(1, 1)
        for i, (text, on) in enumerate(items):
            # 정렬 없이 추가 → 셀(50%) 폭에 꽉 차게
            self.sc_kinds_grid.addWidget(self._kind_chip(text, on), i // 2, i % 2)

    def _kind_chip(self, text: str, on: bool) -> QFrame:
        """검출 항목 칩 — 셀(50%) 폭 꽉참, 모서리 5px. on=크림슨, off=아웃라인."""
        from PySide6.QtWidgets import QSizePolicy
        chip = QFrame(); chip.setObjectName("Chip")
        chip.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        chip.setMinimumHeight(34)
        h = QHBoxLayout(chip)
        h.setContentsMargins(13, 6, 14, 6)
        h.setSpacing(7)
        if on:
            chip.setStyleSheet(f"QFrame#Chip{{background:{BRAND['brand']}; border-radius:5px;}}")
            ic = "check"; iccolor = "#FFFFFF"; tcolor = "#FFFFFF"
        else:
            chip.setStyleSheet("QFrame#Chip{background:#fff; border:1px solid #E7E9EE; border-radius:5px;}")
            ic = "plus"; iccolor = "#8B92A0"; tcolor = "#565E6C"
        icl = QLabel(); icl.setFixedSize(14, 14)
        icl.setPixmap(icons.line_icon(ic, 14, iccolor, 2.6))
        h.addWidget(icl)
        t = QLabel(text)
        t.setStyleSheet(f"color:{tcolor}; font-size:12.5px; font-weight:700; background:transparent;")
        h.addWidget(t)
        h.addStretch()
        return chip

    def _refresh_folder_count(self):
        n = sum(1 for b, _ in self._sc_folders if b.isChecked())
        self.sc_folder_count.setText(f"{n}곳 선택")

    def _add_folder_row(self, path: str, on: bool, label: str | None = None):
        b = QPushButton()
        b.setObjectName("ChkCardG")
        b.setCheckable(True)
        b.setChecked(on)
        b.setCursor(Qt.PointingHandCursor)
        b.setMinimumHeight(46)
        b.setStyleSheet(
            "QPushButton#ChkCardG{background:#fff;border:1px solid #E7E9EE;border-radius:10px;"
            "padding:0;text-align:left;}"
            "QPushButton#ChkCardG:hover{border-color:#D6DAE2;}"
            f"QPushButton#ChkCardG:checked{{border:1px solid {BRAND['brand']};background:{BRAND['pink50']};}}")
        h = QHBoxLayout(b); h.setContentsMargins(13, 9, 13, 9); h.setSpacing(11)
        chk = QLabel(); chk.setFixedSize(20, 20); chk.setPixmap(_checkbox_pixmap(on))
        h.addWidget(chk)
        fic = QLabel(); fic.setPixmap(icons.line_icon("folder", 16, "#565E6C", 2))
        fic.setFixedSize(16, 16)
        h.addWidget(fic)
        pl = QLabel(label or path)
        pl.setStyleSheet("color:#14161C; font-family:'JetBrains Mono','D2Coding',monospace;"
                         "font-size:12px; background:transparent;")
        h.addWidget(pl); h.addStretch()
        b.toggled.connect(lambda c, cb=chk: (cb.setPixmap(_checkbox_pixmap(c)),
                                             self._refresh_folder_count()))
        self.sc_folder_box.addWidget(b)
        self._sc_folders.append((b, path))

    def _add_scan_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "폴더 추가")
        if folder:
            self._add_folder_row(folder, True)

    def _begin_scan(self):
        raw = [p for b, p in self._sc_folders if b.isChecked()]
        if not raw:
            self._warn("스캔 폴더 필요", "스캔할 폴더를 한 곳 이상 선택하세요.")
            return
        # "전체 드라이브 (C:\)" 가상 항목은 실제 C 드라이브로 변환
        folders = ["C:\\" if p.startswith("전체 드라이브") else p for p in raw]
        self._scan_folders_used = folders
        # 사용자가 고른 실제 폴더를 다음 점검 기본값으로 저장(가상 항목 제외).
        real = [p for p in raw if not p.startswith("전체 드라이브")]
        if real and self.cfg is not None:
            self.cfg.target_folders = real
            try:
                self.cfg.save()
            except Exception:
                pass
        self.stack.setCurrentWidget(self.scanning)
        self.progress_bar.setValue(0)
        self.pct_label.setText("0%")
        self._scan_log = []
        self.min_pct.setText("0%"); self.min_bar.setValue(0)
        self.min_found.setText("발견 0건"); self.min_log.setText("")
        self.scan_ring.set(0, 0, "준비 중")
        self.radial_path.setText("준비 중...")
        self.pause_btn.setText("  일시정지")
        self.pause_btn.setIcon(QIcon(icons.line_icon("pause", 15, "#565E6C")))
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
        found = sum(buckets.values())
        eta = max(0, round((total - done) * 0.0015)) if total else 0
        stage = 0 if pct < 10 else (1 if pct < 86 else 2)
        stage_name = ["파일 수집", "내용 검사", "검증·분석"][stage]
        # 막대형
        self.progress_bar.setMaximum(total or 1)
        self.progress_bar.setValue(done)
        self.pct_label.setText(f"{pct}%")
        self.progress_path.setText(f"검사 중  {path}")
        self.scan_sub.setText(
            f"{stage_name} · 검사 {done:,} / {total:,}개 · 예상 남은 시간 약 {eta}초")
        for i, (fr, box, tl, icn) in enumerate(self._stage_labels):
            if i < stage:        # 완료
                txt, bg, bd = "#14161C", "#FFFFFF", "#E7E9EE"
                box.setStyleSheet("background:#15A34A; border-radius:7px;")
                box.setPixmap(icons.line_icon("check", 15, "#FFFFFF", 3))
            elif i == stage:     # 진행
                txt, bg, bd = "#B0123F", "#FCEFF3", "#F6D2DE"
                box.setStyleSheet("background:#B0123F; border-radius:7px;")
                box.setPixmap(icons.line_icon(icn, 15, "#FFFFFF"))
            else:                # 대기
                txt, bg, bd = "#8B92A0", "#F7F8FA", "#E7E9EE"
                box.setStyleSheet("background:#E7E9EE; border-radius:7px;")
                box.setPixmap(icons.line_icon(icn, 15, "#8B92A0"))
            fr.setStyleSheet(f"QFrame#StageCard{{background:{bg};border:1px solid {bd};border-radius:10px;}}")
            tl.setStyleSheet(f"font-weight:700; font-size:13px; color:{txt};")
        # 원형
        self.scan_ring.set(pct, found, stage_name)
        self.radial_path.setText(str(path))
        # 미니멀
        self.min_pct.setText(f"{pct}%")
        self.min_bar.setMaximum(total or 1); self.min_bar.setValue(done)
        self.min_found.setText(f"발견 {found}건")
        from pathlib import Path as _P
        self._scan_log.append(_P(path).name)
        self._scan_log = self._scan_log[-8:]
        rows_html = []
        for j, n in enumerate(self._scan_log):
            last = j == len(self._scan_log) - 1
            col = "#FFC9D8" if last else "rgba(255,255,255,0.4)"
            rows_html.append(
                f'<div style="color:{col};padding:2px 0;">'
                f'<span style="color:#15A34A;">✓</span> scanned&nbsp;&nbsp;{n}</div>')
        self.min_log.setText("".join(rows_html))
        # 버킷(공유)
        for key, v in self._bucket_labels.items():
            n = buckets.get(key, 0)
            color = v.property("color") if n else "#8B92A0"
            v.setText(str(n))
            v.setStyleSheet(f"font-size:26px; font-weight:800; color:{color};")
        self.ocr_note.setVisible(self.ocr_check.isChecked() if hasattr(self, "ocr_check") else False)

    def _on_finished(self, summary):
        self.file_results = summary.file_results
        self._viewing_history = False
        skipped = summary.skipped
        total = summary.total_findings
        grade = summary.risk_grade
        self._scan_grade = grade
        self._action_counts = {"mask": 0, "quarantine": 0, "delete": 0}
        # 결과를 디스크에 저장 → 점검 이력에서 다시 열어 상세·조치할 수 있음.
        try:
            from . import results_store
            self._last_scan_id = results_store.save_scan(
                self.profiles, getattr(self, "_scan_folders_used", []), summary)
        except Exception:
            pass
        # 스캔 완료를 감사 로그에 기록(점검 이력 표시용)
        try:
            from . import actions as _A
            scanned = len(summary.file_results)
            _A.write_audit(
                "closing" if getattr(self, "_closing_mode", False) else "scan",
                "", "success",
                {"files": scanned, "findings": total,
                 "profile": ", ".join(self.profiles), "grade": grade})
        except Exception:
            pass
        # 위험도별 카운트
        bysev = {"높음": 0, "중간": 0, "낮음": 0}
        for r in summary.file_results:
            for f in r.findings:
                bysev[f.severity.value] = bysev.get(f.severity.value, 0) + 1
        # 마지막 점검 요약을 영속화(대시보드 표시용)
        from datetime import datetime
        prev_total = (self.cfg.last_scan or {}).get("total") if self.cfg else None
        if self.cfg is not None:
            self.cfg.last_scan = {
                "at": datetime.now().isoformat(timespec="seconds"),
                "scanned": summary.scanned, "total": total, "skipped": skipped,
                "bysev": bysev, "grade": grade, "prev_total": prev_total}
            self.cfg.last_grade = {"위험": "danger", "주의": "warn", "안전": "safe"}.get(grade, "safe")
            try:
                self.cfg.save()
            except Exception:
                pass
        self._refresh_dashboard()

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
            self._success(
                "점검 완료",
                f"안전합니다 — 점검한 {summary.scanned}개 파일에서 위험을 찾지 못했어요.")
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
        self.row_index = []
        self.tbl_rows = []
        while self.tbl_list.count() > 1:
            it = self.tbl_list.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        counts = {"높음": 0, "중간": 0, "낮음": 0}
        # 전역 위험도순 정렬 — 가장 위험한(높음) 항목이 항상 목록 최상단에 온다.
        _SEV_RANK = {"높음": 0, "중간": 1, "낮음": 2}
        flat = [(Path(r.path), f) for r in results for f in r.findings]
        flat.sort(key=lambda pf: (
            _SEV_RANK.get(pf[1].severity.value, 9), str(pf[0]),
            getattr(pf[1], "line", 0), getattr(pf[1], "start", 0)))
        idx = 0
        for path, f in flat:
            counts[f.severity.value] = counts.get(f.severity.value, 0) + 1
            roww, chk = self._table_row(path, f)
            self.tbl_list.insertWidget(idx, roww)
            self.tbl_rows.append({
                "w": roww, "chk": chk, "path": path, "f": f,
                "sev": f.severity.value,
                "text": f"{path} {f.info_type} {f.masked}".lower()})
            self.row_index.append((path, f))
            idx += 1
        # 필터 칩 카운트
        for k in ["높음", "중간", "낮음"]:
            self._sev_buttons[k].setText(f"{k} {counts[k]}")
        self._populate_group(results)
        self._populate_cards(results)
        if hasattr(self, "tbl_all"):
            self.tbl_all.setChecked(False)
        # 미리보기 숨김(행 선택 시 상단에 표시)
        if hasattr(self, "preview"):
            self.preview.setVisible(False)
        self._set_sev_filter("전체")

    def _clear_layout(self, box, keep_stretch=False):
        while box.count():
            it = box.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        if keep_stretch:
            box.addStretch()

    def _icon_btn(self, name, tip, slot) -> QPushButton:
        b = QPushButton()
        b.setToolTip(tip)
        b.setFixedSize(30, 30)
        b.setIcon(QIcon(icons.line_icon(name, 16, "#565E6C")))
        b.setIconSize(QSize(16, 16))
        b.setCursor(Qt.PointingHandCursor)
        b.setStyleSheet("QPushButton{border:1px solid #E7E9EE;border-radius:8px;background:#fff;}"
                        "QPushButton:hover{background:#F7F8FA;}")
        b.clicked.connect(slot)
        return b

    def _populate_group(self, results):
        # 기존 제거(끝 stretch 유지)
        while self.group_box.count():
            it = self.group_box.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        for r in results:
            if not r.findings:
                continue
            path = Path(r.path)
            top_sev = max((f.severity.value for f in r.findings),
                          key=lambda s: {"높음": 3, "중간": 2, "낮음": 1}.get(s, 0))
            card = _card(shadow=False)
            cv = QVBoxLayout(card)
            cv.setContentsMargins(16, 12, 16, 12)
            cv.setSpacing(8)
            hd = QHBoxLayout()
            fic = QLabel()
            fic.setPixmap(icons.line_icon("fileText", 16, "#565E6C"))
            hd.addWidget(fic)
            fn = QLabel(path.name)
            fn.setStyleSheet("font-weight:800; font-size:14px;")
            hd.addWidget(fn)
            chip = QLabel(); self._style_sev_label(chip, top_sev)
            hd.addWidget(chip)
            hd.addWidget(QLabel(f"{len(r.findings)}건"))
            hd.addStretch()
            hd.addWidget(self._icon_btn("lock", "전체 격리", lambda _=False, p=path, fs=list(r.findings): self._do_action("quarantine", p, fs)))
            hd.addWidget(self._icon_btn("trash", "삭제", lambda _=False, p=path, fs=list(r.findings): self._do_action("delete", p, fs)))
            cv.addLayout(hd)
            pl = QLabel(str(path)); pl.setStyleSheet("color:#8B92A0; font-size:11px;")
            cv.addWidget(pl)
            for f in r.findings:
                roww = QHBoxLayout()
                k = QLabel(f.info_type); k.setStyleSheet("font-size:12.5px;")
                k.setFixedWidth(120)
                roww.addWidget(k)
                mv = QLabel(f.masked)
                mv.setStyleSheet("font-family:'JetBrains Mono',monospace; font-size:12px; color:#14161C;")
                roww.addWidget(mv, 1)
                ln = QLabel(f"line {f.line}"); ln.setStyleSheet("color:#8B92A0; font-size:11px;")
                roww.addWidget(ln)
                c2 = QLabel(); self._style_sev_label(c2, f.severity.value)
                roww.addWidget(c2)
                roww.addWidget(self._icon_btn("eyeOff", "마스킹", lambda _=False, p=path, fs=list(r.findings): self._do_action("mask", p, fs)))
                roww.addWidget(self._icon_btn("lock", "격리", lambda _=False, p=path, fs=list(r.findings): self._do_action("quarantine", p, fs)))
                cv.addLayout(roww)
            self.group_box.addWidget(card)
        self.group_box.addStretch()

    def _populate_cards(self, results):
        for box in self._cards_col_box.values():
            self._clear_layout(box)
        border = {"높음": "#B0123F", "중간": "#E08600", "낮음": "#15A34A"}
        for r in results:
            path = Path(r.path)
            for f in r.findings:
                card = QFrame(); card.setObjectName("FindCard")
                card.setStyleSheet(
                    f"QFrame#FindCard{{background:#fff;border:1px solid #E7E9EE;border-left:3px solid "
                    f"{border.get(f.severity.value,'#E7E9EE')};border-radius:12px;}}")
                cv = QVBoxLayout(card)
                cv.setContentsMargins(14, 12, 14, 12)
                cv.setSpacing(4)
                nmrow = QHBoxLayout(); nmrow.setSpacing(6)
                nm = QLabel(f.info_type)
                nm.setStyleSheet("font-weight:800; font-size:13px;")
                nmrow.addWidget(nm)
                if f.field:  # 표/JSON 구조에서 검출 — 출처 열 라벨
                    fldc = QLabel(f.field)
                    fldc.setStyleSheet(
                        "background:#FCEFF3; color:#B0123F; border-radius:3px;"
                        "padding:0 6px; font-size:10.5px; font-weight:700;")
                    from PySide6.QtWidgets import QSizePolicy
                    fldc.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
                    nmrow.addWidget(fldc)
                nmrow.addStretch()
                cv.addLayout(nmrow)
                mv = QLabel(f.masked)
                mv.setStyleSheet("font-family:'JetBrains Mono',monospace; font-size:13px;")
                cv.addWidget(mv)
                fnm = QLabel(path.name + (f" · 열 “{f.field}”" if f.field else ""))
                fnm.setStyleSheet("color:#8B92A0; font-size:11px;")
                cv.addWidget(fnm)
                ab = QHBoxLayout()
                ab.addStretch()
                ab.addWidget(self._icon_btn("eyeOff", "마스킹", lambda _=False, p=path, fs=list(r.findings): self._do_action("mask", p, fs)))
                ab.addWidget(self._icon_btn("lock", "격리", lambda _=False, p=path, fs=list(r.findings): self._do_action("quarantine", p, fs)))
                ab.addWidget(self._icon_btn("trash", "삭제", lambda _=False, p=path, fs=list(r.findings): self._do_action("delete", p, fs)))
                cv.addLayout(ab)
                self._cards_col_box.get(f.severity.value, self._cards_col_box["낮음"]).addWidget(card)

    def _open_finding(self, path, line: int = 0):
        """검출된 파일을 연다. 텍스트/소스 파일이면 에디터에서 해당 줄로 점프.

        그 외(문서·이미지 등)나 에디터가 없으면 OS 기본 앱으로 연다."""
        import os
        import shutil
        import subprocess as sp
        p = Path(path)
        if not p.exists():
            self._toast("파일을 찾을 수 없습니다(이동·삭제됐을 수 있어요).")
            return
        from .extractors import SUPPORTED_TEXT
        if line and p.suffix.lower() in SUPPORTED_TEXT:
            for name in ("code", "code.cmd"):     # VS Code 가 있으면 줄로 점프
                exe = shutil.which(name)
                if exe:
                    try:
                        sp.Popen([exe, "-g", f"{p}:{line}"])
                        self._toast(f"에디터에서 열었습니다 — line {line}")
                        return
                    except Exception:
                        pass
        try:
            if sys.platform == "win32":
                os.startfile(str(p))  # noqa: S606 - 사용자 의도적 열기
            elif sys.platform == "darwin":
                sp.Popen(["open", str(p)])
            else:
                sp.Popen(["xdg-open", str(p)])
            self._toast(f"파일을 열었습니다 — line {line}" if line else "파일을 열었습니다")
        except Exception:
            self._toast("파일을 열 수 없습니다.")

    def _reveal_file(self, path):
        """탐색기(Finder)에서 해당 파일을 선택한 상태로 폴더를 연다."""
        import subprocess as sp
        p = Path(path)
        if not p.exists():
            self._toast("파일을 찾을 수 없습니다(이동·삭제됐을 수 있어요).")
            return
        try:
            if sys.platform == "win32":
                # 리스트 인자(셸 미경유)로 전달 → 경로 내 특수문자 주입 차단
                sp.Popen(["explorer", f"/select,{p}"])
            elif sys.platform == "darwin":
                sp.Popen(["open", "-R", str(p)])
            else:
                sp.Popen(["xdg-open", str(p.parent)])
        except Exception:
            self._toast("위치를 열 수 없습니다.")

    def _rescan_file_findings(self, path: Path) -> list:
        """파일 1개를 현재 직무 기준으로 재스캔해 검출(원문 포함)을 돌려준다.

        이력에서 마스킹할 때 저장돼 있지 않은 원문(raw)을 복구하는 용도."""
        try:
            from .detection import DetectionEngine
            from .engine import PROFILE_ROLE
            from .scanner import scan_file
            roles = {PROFILE_ROLE[p] for p in self.profiles if p in PROFILE_ROLE}
            wl = list(getattr(self.cfg, "whitelist", []) or [])
            engine = DetectionEngine(roles=roles or None, user_whitelist=wl)
            ocr = bool(self.cfg and getattr(self.cfg, "ocr_mode", "local") != "off")
            return scan_file(Path(path), engine, ocr_enabled=ocr).findings
        except Exception:
            return []

    def _reconstruct_results(self, data: dict) -> list:
        """저장된 스캔 JSON → FileScanResult/Finding 객체 목록(결과 화면 재사용)."""
        from .detection.base import Confidence, Finding, Severity
        from .scanner import FileScanResult
        out = []
        for r in data.get("results", []):
            findings = []
            for d in r.get("findings", []):
                try:
                    findings.append(Finding(
                        detector=d.get("detector", ""),
                        info_type=d.get("info_type", ""),
                        severity=Severity(d.get("severity", "낮음")),
                        confidence=Confidence(d.get("confidence", "패턴일치")),
                        raw="", masked=d.get("masked", ""),
                        start=d.get("start", 0), end=d.get("end", 0),
                        line=d.get("line", 0), context="",
                        field=d.get("field", ""), weak=d.get("weak", False)))
                except ValueError:
                    continue
            out.append(FileScanResult(
                path=Path(r.get("path", "")), status=r.get("status", "완료"),
                findings=findings, error=r.get("error", "")))
        return out

    def _open_saved_scan(self, sid: str):
        """점검 이력에서 과거 스캔을 결과 화면으로 다시 연다."""
        from . import results_store
        data = results_store.load_scan(sid)
        if not data:
            self._warn("결과 없음", "저장된 점검 결과를 찾을 수 없습니다.")
            return
        self.file_results = self._reconstruct_results(data)
        self._viewing_history = True
        self._action_counts = {"mask": 0, "quarantine": 0, "delete": 0}
        total = data.get("total", 0)
        skipped = data.get("skipped", 0)
        self.result_title.setText(f"점검 결과 — 위험 {total}건  ·  이력 보기")
        self.result_sub.setText(
            f"{data.get('at', '')} · 검사 {data.get('scanned', 0)} / 검사불가 {skipped}"
            f" · 직무 {', '.join(data.get('profiles', []))}"
            "  ·  미리보기는 항상 마스킹된 형태로만 표시됩니다.")
        self.unread_banner.setVisible(False)
        self._populate_table(self.file_results)
        self._set_result_view("table")
        self._select_nav("history")
        self.stack.setCurrentWidget(self.results)

    def _do_action(self, action: str, path: Path, findings: list):
        from . import actions as A

        def _qmeta():
            """findings 중 가장 위험한 항목의 유형·심각도(격리 메타 표시용)."""
            if not findings:
                return None, None
            order = {"높음": 3, "중간": 2, "낮음": 1}
            top = max(findings, key=lambda f: order.get(f.severity.value, 0))
            return top.info_type, top.severity.value

        if action == "mask":
            # 이력에서 연 결과는 원문(raw)을 저장하지 않으므로, 마스킹 직전
            # 해당 파일을 재스캔해 원문을 복구한다.
            if any(not getattr(f, "raw", "") for f in findings):
                rescanned = self._rescan_file_findings(path)
                if rescanned:
                    findings = rescanned
            r = A.mask_in_text_file(path, findings)
            ok = r.status == "success"
        elif action == "quarantine":
            it, sv = _qmeta()
            ok = A.quarantine_file(path, it, sv).status == "success"
        else:  # delete
            kind = findings[0].info_type if findings else ""
            dlg = DeleteConfirmDialog(self, [(path.name, kind)])
            if dlg.exec() != QDialog.Accepted:
                return
            if dlg.choice == "quarantine":
                it, sv = _qmeta()
                ok = A.quarantine_file(path, it, sv).status == "success"
                if ok:
                    self._action_counts["quarantine"] += 1
                self._render_recent()
                self._toast("격리했습니다." if ok else "처리하지 못했습니다.")
                return
            ok = A.secure_delete(path, confirmed=True).status == "success"
        if ok:
            self._action_counts[action] += 1
        self._render_recent()
        self._toast("완료되었습니다." if ok else "처리하지 못했습니다.")

    # -------------------------------------------------------- 필터/미리보기
    def _apply_filter(self, *_):
        sev = next((k for k, b in self._sev_buttons.items() if b.isChecked()), "전체")
        q = self.search_box.text().strip().lower()
        shown = 0
        for r in getattr(self, "tbl_rows", []):
            show = (sev == "전체" or r["sev"] == sev) and (not q or q in r["text"])
            r["w"].setVisible(show)
            if show:
                shown += 1
        if hasattr(self, "tbl_count"):
            self.tbl_count.setText(f"{shown}건")

    def _show_preview(self, path, f):
        self.preview.setVisible(True)
        self.pv_file.setText(path.name)
        # 긴 경로는 한 줄 가운데 말줄임(전체 경로는 툴팁으로)
        from PySide6.QtGui import QFontMetrics
        fm = QFontMetrics(self.pv_path.font())
        full = f"{path}  ·  line {f.line}"
        self.pv_path.setText(fm.elidedText(full, Qt.ElideMiddle, 292))
        self.pv_path.setToolTip(str(path))
        color, bg, line = SEV_CHIP.get(f.severity.value, ("#8B92A0", "#F1F2F4", "#E7E9EE"))
        self.pv_type.setText(
            f'{f.info_type}　<span style="color:{color};font-weight:700;">● {f.severity.value}</span>'
            f'<br><span style="color:#7A828F;font-size:11px;font-weight:400;">{_type_desc(f.info_type)}</span>')
        self.pv_type.setWordWrap(True)
        self.pv_value.setText(f.masked)
        ctx = f.context or ""
        if f.raw and f.raw in ctx:
            ctx = ctx.replace(f.raw, f.masked)
        self.pv_ctx.setText(ctx or "(문맥 없음)")

    # -------------------------------------------------------- 조치
    def _selected_by_file(self):
        grouped = {}
        for r in getattr(self, "tbl_rows", []):
            if r["chk"].isChecked():
                grouped.setdefault(r["path"], []).append(r["f"])
        return grouped

    def _require(self, grouped):
        if not grouped:
            self._warn("선택 필요", "처리할 행을 선택하세요.")
            return False
        return True

    def _action_mask(self):
        g = self._selected_by_file()
        if not self._require(g):
            return
        from .actions import mask_in_text_file
        ok = sum(1 for p, fs in g.items() if mask_in_text_file(p, fs).status == "success")
        self._action_counts["mask"] += ok
        self._success("마스킹 완료",
                      f"{ok}개 파일의 마스킹 사본(_masked)을 생성했습니다. "
                      "원본에는 개인정보가 그대로 남아 있으니, 필요하면 원본을 격리/삭제하세요.")
        self._render_recent()

    def _action_quarantine(self):
        g = self._selected_by_file()
        if not self._require(g):
            return
        from .actions import quarantine_file
        ok = sum(1 for p in g if quarantine_file(p).status == "success")
        self._action_counts["quarantine"] += ok
        self._success("격리 완료", f"{ok}개 파일을 암호화 격리함으로 옮겼습니다.")
        self._render_recent()

    def _action_delete(self):
        g = self._selected_by_file()
        if not self._require(g):
            return
        items = [(p.name, (fs[0].info_type if fs else "")) for p, fs in g.items()]
        dlg = DeleteConfirmDialog(self, items)
        if dlg.exec() != QDialog.Accepted:
            return
        if dlg.choice == "quarantine":
            from .actions import quarantine_file
            ok = sum(1 for p in g if quarantine_file(p).status == "success")
            self._action_counts["quarantine"] += ok
            self._toast(f"{ok}개 파일을 격리했습니다.")
        else:
            from .actions import secure_delete
            done = sum(1 for p in g if secure_delete(p, confirmed=True).status == "success")
            self._action_counts["delete"] += done
            self._toast(f"{done}개 파일을 영구 삭제했습니다.")
        self._render_recent()

    def _mark_false_positive(self):
        sel = [r for r in getattr(self, "tbl_rows", []) if r["chk"].isChecked()]
        if not sel:
            self._warn("선택 필요", "오탐으로 표시할 행을 선택하세요.")
            return
        from .config import AppConfig
        cfg = self.cfg or AppConfig.load()
        wl = list(cfg.whitelist or [])
        added = 0
        for r in sel:
            raw = r["f"].raw
            if raw not in wl:
                wl.append(raw)
                added += 1
            r["w"].setVisible(False)
        cfg.whitelist = wl
        cfg.save()
        self.cfg = cfg
        self._wl_refresh()  # 설정의 오탐 제외 목록과 동기화
        self._success("오탐 등록",
                      f"{added}건을 오탐(제외)으로 등록했습니다. 다음 점검부터 제외됩니다.")

    def save_report(self):
        if not self.file_results:
            self._warn("점검 필요", "먼저 점검을 실행하세요.")
            return
        ls = (getattr(self.cfg, "last_scan", None) or {}) if self.cfg else {}
        scanned = ls.get("scanned") or len(self.file_results)
        grade = getattr(self, "_scan_grade", ls.get("grade", "안전"))
        dlg = ReportPreviewDialog(
            self, self.file_results, self.profiles, scanned, grade,
            dict(self._action_counts))
        dlg.exec()

    def run_figma_scan(self, url, token, consent):
        from .figma_scan import (
            FigmaApiError, FigmaConsentError, parse_file_key, scan_figma_file)
        try:
            key = parse_file_key(url)
            result = scan_figma_file(key, token, user_consented=consent)
        except FigmaConsentError as e:
            self._warn("동의 필요", str(e))
            return
        except (FigmaApiError, ValueError) as e:
            self._error("Figma 검사 실패", str(e))
            return
        self._notice(
            "Figma 검사 완료",
            f"'{result.file_name}'에서 텍스트 {result.text_node_count}개 검사, "
            f"위험 {len(result.findings)}건 발견")

    def _notice(self, title: str, message: str, kind: str = "info"):
        """앱 디자인 모달 알림(네이티브 QMessageBox 대체)."""
        NoticeDialog(self, title, message, kind).exec()

    def _warn(self, title: str, message: str):
        self._notice(title, message, "warn")

    def _error(self, title: str, message: str):
        self._notice(title, message, "error")

    def _success(self, title: str, message: str):
        self._notice(title, message, "success")

    # -------------------------------------------------------- 업데이트 확인
    def _check_update(self):
        """GitHub Releases 최신 버전과 비교(버튼 클릭 시 1회 조회)."""
        from PySide6.QtCore import QThread, Signal

        self._upd_btn.setEnabled(False)
        self._upd_btn.setText("확인 중...")

        class _Worker(QThread):
            result = Signal(object, str)

            def run(self):
                try:
                    from .updates import check_for_update
                    cur = getattr(__import__("soliguard"), "__version__", "0.0.0")
                    self.result.emit(check_for_update(current=cur), "")
                except Exception as e:  # UpdateError 포함
                    self.result.emit(None, str(e))

        self._upd_worker = _Worker()
        self._upd_worker.result.connect(self._on_update_result)
        self._upd_worker.start()

    def _on_update_result(self, info, error: str):
        self._upd_btn.setEnabled(True)
        self._upd_btn.setText("업데이트 확인")
        if error:
            self._warn("업데이트 확인 실패", error)
            return
        if info.is_newer:
            self._upd_status.setText(f"새 버전 v{info.latest} 있음 (현재 v{info.current})")
            self._upd_status.setStyleSheet("color:#B0123F; font-size:12px; font-weight:700;")
            import webbrowser
            NoticeDialog(
                self, "업데이트 있음",
                f"새 버전 v{info.latest} 이(가) 있습니다. 현재 버전은 v{info.current}입니다.\n"
                "릴리스 페이지에서 최신 설치본을 받을 수 있습니다.",
                kind="info",
                action_label="  릴리스 페이지 열기",
                on_action=lambda u=info.download_url: webbrowser.open(u),
            ).exec()
        else:
            self._upd_status.setText(f"최신 버전을 사용 중입니다 (v{info.current})")
            self._notice("업데이트", f"최신 버전을 사용 중입니다 (v{info.current}).")

    def _toast(self, message: str):
        from PySide6.QtCore import QTimer
        if getattr(self, "_toast_label", None) is None:
            self._toast_label = QLabel(self)
            self._toast_label.setStyleSheet(
                "background:#1B1E25; color:#fff; border-radius:12px;"
                "padding:12px 18px; font-size:13px; font-weight:600;")
            self._toast_label.setAlignment(Qt.AlignCenter)
        t = self._toast_label
        t.setText(message)
        t.adjustSize()
        t.move((self.width() - t.width()) // 2, self.height() - t.height() - 28)
        t.show()
        t.raise_()
        QTimer.singleShot(2400, t.hide)

    def closeEvent(self, event):
        if self._tray_active:
            event.ignore()
            self.hide()
        else:
            event.accept()


def _read_audit_tail(n: int) -> list:
    """감사 로그 마지막 n건을 오래된→최신 순으로(기존 호출부 호환)."""
    try:
        from . import actions
        return list(reversed(actions.read_audit(limit=n)))  # 최신순 → 오래된순
    except Exception:
        return []


def main() -> int:
    import os
    app = QApplication(sys.argv)
    fam = fonts.load_fonts(app)
    app.setWindowIcon(icons.app_icon())
    app.setStyleSheet(build_qss("light"))
    app.setFont(app.font())  # 스타일시트 적용 후 앱 폰트 재확정
    win = MainWindow()
    win.resize(1180, 760)
    win.show()
    shot = os.environ.get("SOLIGUARD_SHOT")
    if shot:
        from PySide6.QtCore import QTimer
        def _grab():
            win.grab().save(shot)
            print("SHOT", fam, win.dash_sub.fontInfo().family())
            app.quit()
        QTimer.singleShot(400, _grab)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
