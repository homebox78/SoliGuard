"""구체 검출기 구현.

표준 검출기(주민/카드/사업자/전화/이메일/계좌)는 base.Detector의 2단계
스캔 루프를 그대로 쓰고, API 키·시크릿 검출기는 여러 규칙을 다루므로
detect()를 직접 재정의한다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterator

from . import validators as V
from .base import Confidence, Detector, Finding, LineIndex, Severity

# 직무 식별자 상수
ROLE_DEVELOPER = "developer"
ROLE_DESIGNER = "designer"
ROLE_PLANNER = "planner"
ROLE_PM = "pm"
ROLE_FINANCE = "finance"


# ---------------------------------------------------------------------------
# 표준 검출기
# ---------------------------------------------------------------------------
class RRNDetector(Detector):
    """주민등록번호/외국인등록번호. 생년월일·성별·체크섬 2차 검증."""

    name = "rrn"
    info_type = "주민등록번호"
    severity = Severity.HIGH
    keep_unverified = False  # 오탐이 치명적이라 검증 통과분만
    field_keywords = ("주민", "주민번호", "주민등록", "외국인등록", "rrn", "ssn")

    _pat = re.compile(r"(?<!\d)\d{6}-?[1-8]\d{6}(?!\d)")

    @property
    def pattern(self) -> re.Pattern[str]:
        return self._pat

    def validate(self, raw: str) -> bool:
        return V.validate_rrn(raw) or V.validate_foreigner_rrn(raw)

    def detected_type(self, raw: str) -> str:
        return "외국인등록번호" if V.rrn_is_foreigner(raw) else "주민등록번호"

    def mask(self, raw: str) -> str:
        d = V.digits_only(raw)
        return f"{d[0:2]}****-{d[6]}******"


class CreditCardDetector(Detector):
    """신용카드 번호. Luhn 알고리즘 2차 검증."""

    name = "credit_card"
    info_type = "신용카드번호"
    severity = Severity.HIGH
    field_keywords = ("카드", "카드번호", "card", "cardno", "pan")

    # 13~19자리, 자리 사이 단일 공백/하이픈 허용
    _pat = re.compile(r"(?<![\w-])\d(?:[ -]?\d){12,18}(?![\w-])")

    @property
    def pattern(self) -> re.Pattern[str]:
        return self._pat

    def validate(self, raw: str) -> bool:
        return V.luhn_valid(raw)

    def mask(self, raw: str) -> str:
        d = V.digits_only(raw)
        return "****-****-****-" + d[-4:]


class BRNDetector(Detector):
    """사업자등록번호. 국세청 체크섬 공식 2차 검증."""

    name = "brn"
    info_type = "사업자등록번호"
    severity = Severity.MEDIUM
    field_keywords = ("사업자", "사업자등록", "brn", "법인")

    _pat = re.compile(r"(?<!\d)\d{3}-?\d{2}-?\d{5}(?!\d)")

    @property
    def pattern(self) -> re.Pattern[str]:
        return self._pat

    def validate(self, raw: str) -> bool:
        return V.validate_brn(raw)

    def mask(self, raw: str) -> str:
        d = V.digits_only(raw)
        return f"{d[0:3]}-**-*****"


class PhoneDetector(Detector):
    """휴대폰/유선 전화번호. 형식·자릿수 검증."""

    name = "phone"
    info_type = "전화번호"
    severity = Severity.MEDIUM
    field_keywords = (
        "전화", "휴대폰", "휴대전화", "핸드폰", "연락처", "phone", "mobile", "tel", "hp",
    )

    _pat = re.compile(
        r"(?<![\d-])(?:01[016789]|0\d{1,2})[ .-]?\d{3,4}[ .-]?\d{4}(?![\d-])"
    )

    @property
    def pattern(self) -> re.Pattern[str]:
        return self._pat

    def validate(self, raw: str) -> bool:
        d = V.digits_only(raw)
        return d.startswith("0") and 9 <= len(d) <= 11

    def mask(self, raw: str) -> str:
        d = V.digits_only(raw)
        return f"{d[:3]}-****-{d[-4:]}"


class EmailDetector(Detector):
    """이메일 주소. 형식 검증."""

    name = "email"
    info_type = "이메일"
    severity = Severity.MEDIUM
    field_keywords = ("이메일", "메일", "email", "e-mail", "mail")

    _pat = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")

    @property
    def pattern(self) -> re.Pattern[str]:
        return self._pat

    def validate(self, raw: str) -> bool:
        local, _, domain = raw.partition("@")
        return bool(local) and "." in domain and not domain.startswith(".")

    def mask(self, raw: str) -> str:
        local, _, domain = raw.partition("@")
        head = local[0] if local else "*"
        return f"{head}{'*' * max(1, len(local) - 1)}@{domain}"


class AccountDetector(Detector):
    """계좌번호(은행). 하이픈 구분 + 자릿수 검증.

    은행별 포맷이 다양해 오탐이 많으므로 '검증 통과분만' 남긴다(keep_unverified=False).
    짧은 숫자열(예: 12-34-5678)이 계좌로 잘못 잡히던 무더기 오탐을 방지한다."""

    name = "account"
    info_type = "계좌번호"
    severity = Severity.MEDIUM
    keep_unverified = False
    field_keywords = ("계좌", "계좌번호", "예금주", "account", "acct", "iban")

    # 3그룹(하이픈 2개) 형태만, 첫 그룹 2~4자리(은행 계좌 형태)
    _pat = re.compile(r"(?<![\d-])\d{2,4}-\d{2,6}-\d{2,6}(?:-\d{1,6})?(?![\d-])")

    @property
    def pattern(self) -> re.Pattern[str]:
        return self._pat

    def validate(self, raw: str) -> bool:
        d = V.digits_only(raw)
        # 11~14자리만 계좌로 인정(10자리는 사업자번호·전화와 충돌해 제외)
        return 11 <= len(d) <= 14 and len(set(d)) > 2

    def mask(self, raw: str) -> str:
        d = V.digits_only(raw)
        return "*" * (len(d) - 4) + d[-4:]


class PassportDetector(Detector):
    """여권번호. 발급기호(영문 1자) + 숫자 8자리 형식·기호 검증."""

    name = "passport"
    info_type = "여권번호"
    severity = Severity.HIGH
    field_keywords = ("여권", "passport", "passportno")

    # 영문 1자 + 숫자 8자(구권/전자여권). 앞뒤 영숫자 경계로 토큰 분리.
    _pat = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]\d{8}(?![A-Za-z0-9])")

    @property
    def pattern(self) -> re.Pattern[str]:
        return self._pat

    def validate(self, raw: str) -> bool:
        return V.validate_passport(raw)

    def mask(self, raw: str) -> str:
        s = raw.strip()
        return f"{s[0]}{s[1:3]}*****"


class DriverLicenseDetector(Detector):
    """운전면허번호. 지역코드(2)-연도(2)-일련(6)-검증(2) 형식·지역 검증."""

    name = "driver_license"
    info_type = "운전면허번호"
    severity = Severity.HIGH
    field_keywords = ("운전면허", "면허번호", "면허", "license", "driver")

    _pat = re.compile(r"(?<!\d)\d{2}-?\d{2}-?\d{6}-?\d{2}(?!\d)")

    @property
    def pattern(self) -> re.Pattern[str]:
        return self._pat

    def validate(self, raw: str) -> bool:
        return V.validate_driver_license(raw)

    def mask(self, raw: str) -> str:
        d = V.digits_only(raw)
        return f"{d[0:2]}-{d[2:4]}-******-**"


class IPDetector(Detector):
    """IPv4 주소. 옥텟 범위 검증(개발자 직무 특화, 단독 위험 낮아 LOW)."""

    name = "ip"
    info_type = "IP 주소"
    severity = Severity.LOW
    default_roles = frozenset({ROLE_DEVELOPER})
    field_keywords = ("ip", "아이피", "ipaddr", "host", "서버")

    _pat = re.compile(r"(?<![\d.])\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?![\d.])")

    @property
    def pattern(self) -> re.Pattern[str]:
        return self._pat

    def validate(self, raw: str) -> bool:
        return V.valid_ipv4(raw)

    def mask(self, raw: str) -> str:
        parts = raw.strip().split(".")
        return f"{parts[0]}.{parts[1]}.*.*" if len(parts) == 4 else "*.*.*.*"


class AddressDetector(Detector):
    """한국 도로명/지번 주소(시/도 + 시군구 + 도로·동 + 번지). 단독 노출 LOW."""

    name = "address"
    info_type = "주소"
    severity = Severity.LOW
    field_keywords = ("주소", "거주지", "address", "addr", "소재지")

    _SIDO = (
        r"서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충청북도|충청남도|충북|충남"
        r"|전라북도|전라남도|전북|전남|경상북도|경상남도|경북|경남|제주"
    )
    _pat = re.compile(
        rf"(?:{_SIDO})(?:특별시|광역시|특별자치시|특별자치도|도)?\s*"
        r"[가-힣]{1,10}(?:시|군|구)\s*"
        r"[가-힣A-Za-z0-9]{1,20}(?:읍|면|동|리|로|길|가)\s*"
        r"\d{1,4}(?:-\d{1,4})?"
    )

    @property
    def pattern(self) -> re.Pattern[str]:
        return self._pat

    def validate(self, raw: str) -> bool:
        # 전체 패턴이 일치했다는 것 자체가 강한 구조적 증거(체크섬 없음)
        return True

    def mask(self, raw: str) -> str:
        s = raw.strip()
        head = s[:6]
        return head + "*" * max(2, len(s) - len(head))


# ---------------------------------------------------------------------------
# API 키 / 시크릿 / DB 접속정보 검출기 (개발자 직무 특화)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SecretRule:
    """시크릿 검출 규칙 하나."""

    name: str
    info_type: str
    regex: re.Pattern[str]
    value_group: int | None  # 시크릿 값이 담긴 그룹 번호(None이면 전체 매치)
    min_entropy: float = 0.0  # 이 엔트로피 이상이면 VERIFIED


class SecretDetector(Detector):
    """소스코드·설정 파일 내 API 키, 시크릿, DB 접속정보, 하드코딩 비밀번호.

    키워드 + 패턴으로 후보를 찾고, 값의 Shannon 엔트로피로 진위를 가린다.
    이것이 일반 무료 도구가 다루지 못하는 SI 산출물(소스코드) 검출의 핵심.
    """

    name = "secret"
    info_type = "API 키/시크릿"
    severity = Severity.HIGH
    default_roles = frozenset({ROLE_DEVELOPER})

    _RULES: tuple[SecretRule, ...] = (
        SecretRule(
            "aws_access_key",
            "AWS Access Key",
            re.compile(r"(?<![A-Z0-9])(?:AKIA|ASIA|AGPA|AIDA)[0-9A-Z]{16}(?![A-Z0-9])"),
            value_group=None,
        ),
        SecretRule(
            "private_key",
            "개인키(PEM)",
            re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
            value_group=None,
        ),
        SecretRule(
            "db_url",
            "DB 접속정보",
            re.compile(
                r"(?i)(?:jdbc:)?(?:mysql|postgresql|postgres|mongodb|oracle|mariadb|sqlserver)"
                r":\/\/[^\s'\"]*:[^\s'\"]+@[^\s'\"]+"
            ),
            value_group=None,
        ),
        SecretRule(
            "assigned_secret",
            "API 키/시크릿",
            re.compile(
                r"""(?ix)
                \b(api[_-]?key|secret[_-]?key|secret|access[_-]?token|auth[_-]?token
                  |token|client[_-]?secret|password|passwd|pwd)
                \s*[:=]\s*
                ['"]?
                ([A-Za-z0-9+/=_\-.]{8,})
                ['"]?
                """
            ),
            value_group=2,
            min_entropy=3.0,
        ),
    )

    def detect(self, text: str, line_index: LineIndex) -> Iterator[Finding]:
        for rule in self._RULES:
            for m in rule.regex.finditer(text):
                if rule.value_group is None:
                    value = m.group(0)
                    v_start, v_end = m.start(), m.end()
                else:
                    value = m.group(rule.value_group)
                    v_start = m.start(rule.value_group)
                    v_end = m.end(rule.value_group)

                # 엔트로피 기반 진위 판정
                if rule.min_entropy > 0:
                    entropy = V.shannon_entropy(value)
                    verified = entropy >= rule.min_entropy
                else:
                    verified = True

                confidence = (
                    Confidence.VERIFIED if verified else Confidence.PATTERN_ONLY
                )
                severity = self.severity if verified else Severity.MEDIUM

                yield Finding(
                    detector=self.name,
                    info_type=rule.info_type,
                    severity=severity,
                    confidence=confidence,
                    raw=m.group(0),
                    masked=self._mask_value(
                        m.group(0), value, v_start - m.start(), v_end - m.start()
                    ),
                    start=m.start(),
                    end=m.end(),
                    line=line_index.line_of(m.start()),
                    context="",  # 시크릿은 문맥에도 값이 섞일 수 있어 비움
                )

    @staticmethod
    def _mask_value(full_match: str, value: str, rel_start: int, rel_end: int) -> str:
        """시크릿 값 구간만 위치 기반으로 마스킹한다(키 이름과 값이 같아도 안전)."""
        # 충분히 긴 값만 식별용으로 앞 4자 노출, 짧은 값은 전부 가린다.
        head = value[:4] if len(value) >= 12 else ""
        masked_value = head + "*" * max(4, len(value) - len(head))
        return full_match[:rel_start] + masked_value + full_match[rel_end:]


#: 엔진이 기본 등록하는 검출기 목록(순서 = 스팬 중복 시 우선순위)
DEFAULT_DETECTORS: tuple[type[Detector], ...] = (
    RRNDetector,            # 주민/외국인등록번호
    BRNDetector,            # 사업자등록번호
    CreditCardDetector,     # 신용카드
    PassportDetector,       # 여권번호
    DriverLicenseDetector,  # 운전면허(계좌보다 우선해 12자리 오인식 방지)
    SecretDetector,         # API 키/시크릿(개발자)
    PhoneDetector,          # 전화번호(계좌보다 우선)
    AccountDetector,        # 계좌번호
    IPDetector,             # IP 주소(개발자)
    EmailDetector,          # 이메일
    AddressDetector,        # 주소(가장 낮은 우선순위)
)
