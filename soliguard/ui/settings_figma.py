"""설정 화면의 'Figma 클라우드 검사(고급)' 섹션 - 옵트인 UI.

핵심: 동의 체크 + 토큰 + URL 세 조건이 모두 충족되기 전에는 검사 버튼이 비활성.
토큰은 비밀번호 모드로 표시하고 섹션을 접으면 초기화해 화면·메모리 잔존을 막는다.
이는 figma_scan.py 의 코드 레벨 가드(FigmaConsentError)와 이중으로 작동한다.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QVBoxLayout,
)


class FigmaOptInSection(QGroupBox):
    """기본 비활성(접힘). 동의+토큰+URL 모두 충족 시에만 검사 버튼 활성화."""

    scan_requested = Signal(str, str, bool)  # (url, token, consent)

    def __init__(self):
        super().__init__("Figma 클라우드 검사 (고급)")
        self.setCheckable(True)
        self.setChecked(False)
        self._build()
        self.toggled.connect(self._on_section_toggled)

    def _build(self) -> None:
        lay = QVBoxLayout(self)

        notice = QLabel(
            "⚠ 이 기능은 Figma 서버에서 디자인의 텍스트를 가져옵니다.\n"
            "가져온 내용은 검사 직후 즉시 폐기되며 PC에 저장되지 않습니다.\n"
            "이미지·디자인 원본은 내려받지 않고 텍스트만 검사합니다."
        )
        notice.setStyleSheet("color:#D97706; font-size:12px;")
        notice.setWordWrap(True)
        lay.addWidget(notice)

        self.consent = QCheckBox(
            "위 내용을 이해했으며, Figma에서 텍스트를 가져오는 데 동의합니다."
        )
        self.consent.stateChanged.connect(self._update_button)
        lay.addWidget(self.consent)

        token_row = QHBoxLayout()
        token_row.addWidget(QLabel("액세스 토큰"))
        self.token = QLineEdit()
        self.token.setEchoMode(QLineEdit.Password)
        self.token.setPlaceholderText("figd_... (Figma 개인 액세스 토큰)")
        self.token.textChanged.connect(self._update_button)
        token_row.addWidget(self.token)
        lay.addLayout(token_row)

        url_row = QHBoxLayout()
        url_row.addWidget(QLabel("파일 URL"))
        self.url = QLineEdit()
        self.url.setPlaceholderText("https://www.figma.com/file/.../...")
        self.url.textChanged.connect(self._update_button)
        url_row.addWidget(self.url)
        lay.addLayout(url_row)

        self.scan_btn = QPushButton("Figma 파일 검사")
        self.scan_btn.setObjectName("Primary")
        self.scan_btn.setEnabled(False)
        self.scan_btn.clicked.connect(self._on_scan)
        lay.addWidget(self.scan_btn, alignment=Qt.AlignRight)

        help_lbl = QLabel(
            '<a href="https://www.figma.com/developers/api#access-tokens">'
            "토큰 발급 방법 보기</a>"
        )
        help_lbl.setOpenExternalLinks(True)
        help_lbl.setStyleSheet("font-size:12px;")
        lay.addWidget(help_lbl)

    def _on_section_toggled(self, on: bool) -> None:
        if not on:  # 섹션 접으면 입력 초기화(토큰 잔존 방지)
            self.consent.setChecked(False)
            self.token.clear()
            self.url.clear()
            self.scan_btn.setEnabled(False)

    def _update_button(self) -> None:
        ready = (
            self.consent.isChecked()
            and bool(self.token.text().strip())
            and bool(self.url.text().strip())
        )
        self.scan_btn.setEnabled(ready)

    def _on_scan(self) -> None:
        consent = self.consent.isChecked()
        token = self.token.text().strip()
        url = self.url.text().strip()
        if not (consent and token and url):
            QMessageBox.warning(self, "확인", "동의·토큰·URL을 모두 입력하세요.")
            return
        self.scan_requested.emit(url, token, consent)
