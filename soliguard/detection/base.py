"""검출 엔진의 핵심 자료구조와 Detector 추상 기반 클래스."""

from __future__ import annotations

import enum
import re
from abc import ABC
from dataclasses import dataclass, field
from typing import Iterator


class Severity(enum.Enum):
    """검출 항목의 위험도. 화면설계서의 색/아이콘과 매핑된다."""

    HIGH = "높음"    # 🔴 주민번호, 카드번호, API 키, DB 접속정보
    MEDIUM = "중간"  # 🟡 전화, 이메일, 계좌
    LOW = "낮음"     # 🟢 단독 노출 시 위험이 낮은 항목


class Confidence(enum.Enum):
    """2단계 검출 결과에 대한 신뢰도.

    - VERIFIED: 1차 정규식 + 2차 검증을 모두 통과(진짜일 가능성 높음)
    - PATTERN_ONLY: 1차 정규식만 통과, 2차 검증 실패 또는 미적용
    """

    VERIFIED = "검증됨"
    PATTERN_ONLY = "패턴일치"


@dataclass(frozen=True)
class Finding:
    """검출된 개인정보 한 건.

    원문(raw)은 조치 단계에서만 사용하고, 화면 노출 시에는 masked를
    사용한다(화면설계서: 미리보기는 항상 마스킹된 형태로만 노출).
    """

    detector: str          # 검출기 식별자 (예: "rrn")
    info_type: str         # 한국어 정보 유형명 (예: "주민등록번호")
    severity: Severity
    confidence: Confidence
    raw: str               # 원문 매치 (조치 전용, 화면 노출 금지)
    masked: str            # 마스킹된 표시용 문자열
    start: int             # 원문 내 시작 오프셋
    end: int               # 원문 내 끝 오프셋
    line: int              # 1-기반 줄 번호
    context: str = ""      # 주변 문맥(추후 AI 판단용), 화면 노출 금지
    field: str = ""        # 구조화 포맷(표/JSON)의 소속 필드 라벨(컬럼 헤더 등)
    weak: bool = False      # 형식만 일치(2차 검증 실패) → 엔진이 보존 여부 결정

    def __repr__(self) -> str:  # 디버깅 시에도 원문이 새지 않도록 마스킹만 노출
        return (
            f"Finding({self.detector}, {self.confidence.value}, "
            f"line={self.line}, {self.masked!r})"
        )


class Detector(ABC):
    """모든 검출기의 추상 기반 클래스.

    표준 검출기는 1차 정규식(`pattern`)과 2차 검증(`validate`),
    마스킹(`mask`)만 구현하면 된다. 2단계 스캔 루프(`detect`)는 여기서
    제공한다. API 키처럼 여러 규칙을 쓰는 검출기는 `detect`를 직접
    재정의한다.
    """

    #: 검출기 식별자(영문 소문자)
    name: str = ""
    #: 화면 표시용 한국어 정보 유형명
    info_type: str = ""
    #: 기본 위험도
    severity: Severity = Severity.MEDIUM
    #: 이 검출기를 기본 활성화하는 직무 집합(빈 집합이면 전 직무 공통)
    default_roles: frozenset[str] = frozenset()
    #: 2차 검증 실패(PATTERN_ONLY) 후보도 결과에 남길지 여부
    keep_unverified: bool = False
    #: 구조화 필드(컬럼 헤더·JSON 키)에 이 부분문자열이 있으면 이 검출기의
    #: 유형으로 강하게 추정 → 검증 실패 후보도 '필드 보강'으로 구제한다.
    field_keywords: tuple[str, ...] = ()

    @property
    def pattern(self) -> re.Pattern[str]:
        """1차 탐지용 컴파일된 정규식(표준 검출기에서 구현)."""
        raise NotImplementedError

    def validate(self, raw: str) -> bool:
        """2차 검증. 진짜 유효한 값이면 True(표준 검출기에서 구현)."""
        raise NotImplementedError

    def mask(self, raw: str) -> str:
        """검출 부분을 마스킹한 표시용 문자열(표준 검출기에서 구현)."""
        raise NotImplementedError

    def detect(self, text: str, line_index: "LineIndex") -> Iterator[Finding]:
        """2단계 스캔: 정규식으로 후보를 찾고 각 후보를 검증한다.

        검증 실패(weak) 후보도 항상 내보낸다. 최종 보존 여부는 엔진이
        결정한다(keep_unverified 또는 소속 필드 라벨 일치 시 구제).
        """
        for m in self.pattern.finditer(text):
            raw = m.group(0)
            verified = self.validate(raw)
            confidence = (
                Confidence.VERIFIED if verified else Confidence.PATTERN_ONLY
            )
            # 검증 실패한 후보는 한 단계 낮은 위험도로 강등(필드 구제 시 엔진이 복원)
            severity = self.severity
            if not verified and severity is Severity.HIGH:
                severity = Severity.MEDIUM

            start = m.start()
            yield Finding(
                detector=self.name,
                info_type=self.detected_type(raw),
                severity=severity,
                confidence=confidence,
                raw=raw,
                masked=self.mask(raw),
                start=start,
                end=m.end(),
                line=line_index.line_of(start),
                context=_context(text, start, m.end()),
                weak=not verified,
            )

    def detected_type(self, raw: str) -> str:
        """이 매치의 한국어 정보 유형명. 매치 내용에 따라 분기할 검출기는 재정의."""
        return self.info_type


@dataclass
class LineIndex:
    """오프셋 -> 줄 번호 변환을 O(log n)으로 처리하기 위한 보조 인덱스."""

    _newline_offsets: list[int] = field(default_factory=list)

    @classmethod
    def build(cls, text: str) -> "LineIndex":
        offsets = [i for i, ch in enumerate(text) if ch == "\n"]
        return cls(offsets)

    def line_of(self, offset: int) -> int:
        import bisect

        return bisect.bisect_right(self._newline_offsets, offset) + 1


def _context(text: str, start: int, end: int, window: int = 40) -> str:
    """검출 위치 주변 문맥을 추출(추후 문맥 기반 AI 판단용)."""
    left = max(0, start - window)
    right = min(len(text), end + window)
    snippet = text[left:right].replace("\n", " ").strip()
    return snippet
