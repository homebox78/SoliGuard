"""검출 엔진 오케스트레이터.

여러 검출기를 등록하고, 텍스트/파일을 2단계로 스캔한 뒤,
화이트리스트 필터링과 중복 스팬 정리를 거쳐 Finding 목록을 돌려준다.

직무(role)별로 활성 검출기를 다르게 구성해 '직무별 스캔 프로파일'
(기획서 5장 차별점 #1)의 검출 엔진 측 기반을 제공한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .base import Confidence, Detector, Finding, LineIndex, Severity
from .detectors import DEFAULT_DETECTORS
from .whitelist import is_dummy

__all__ = ["DetectionEngine", "ScanSummary"]

# 최종 정렬용 위험도 가중치(높을수록 먼저)
_SEVERITY_ORDER = {Severity.HIGH: 0, Severity.MEDIUM: 1, Severity.LOW: 2}


@dataclass
class ScanSummary:
    """대시보드/리포트용 집계 결과."""

    total: int
    by_severity: dict[str, int]
    by_type: dict[str, int]
    verified: int
    pattern_only: int

    def risk_grade(self) -> str:
        """화면설계서의 안전🟢/주의🟡/위험🔴 3단계 등급."""
        if self.by_severity.get(Severity.HIGH.value, 0) > 0:
            return "위험"
        if self.total > 0:
            return "주의"
        return "안전"


class DetectionEngine:
    def __init__(
        self,
        detectors: Sequence[Detector] | None = None,
        role: str | None = None,
        enabled_types: Iterable[str] | None = None,
    ) -> None:
        """엔진 생성.

        :param detectors: 사용할 검출기 인스턴스(기본: DEFAULT_DETECTORS 전체)
        :param role: 직무. 지정 시 해당 직무의 기본 검출기만 활성화한다.
        :param enabled_types: 활성화할 검출기 name 집합(role보다 우선)
        """
        if detectors is None:
            detectors = [cls() for cls in DEFAULT_DETECTORS]
        # 등록 순서 = 중복 스팬 우선순위
        self._all: list[Detector] = list(detectors)
        self._rank = {d.name: i for i, d in enumerate(self._all)}

        if enabled_types is not None:
            wanted = set(enabled_types)
            self._active = [d for d in self._all if d.name in wanted]
        elif role is not None:
            self._active = [d for d in self._all if self._role_default(d, role)]
        else:
            self._active = list(self._all)

    @staticmethod
    def _role_default(detector: Detector, role: str) -> bool:
        """공통 검출기(default_roles 비어 있음)는 항상, 특화 검출기는 해당 직무만."""
        if not detector.default_roles:
            return True
        return role in detector.default_roles

    @property
    def active_detectors(self) -> list[str]:
        return [d.name for d in self._active]

    # ------------------------------------------------------------------
    # 스캔
    # ------------------------------------------------------------------
    def scan_text(self, text: str) -> list[Finding]:
        """주어진 텍스트를 스캔해 정리된 Finding 목록을 반환."""
        line_index = LineIndex.build(text)
        raw_findings: list[Finding] = []
        for det in self._active:
            for finding in det.detect(text, line_index):
                if is_dummy(finding.detector, finding.raw):
                    continue
                raw_findings.append(finding)

        resolved = self._resolve_overlaps(raw_findings)
        resolved.sort(
            key=lambda f: (_SEVERITY_ORDER[f.severity], f.line, f.start)
        )
        return resolved

    def scan_file(self, path: str | Path, encoding: str = "utf-8") -> list[Finding]:
        """텍스트 파일 하나를 스캔(PoC: 평문 디코딩만).

        실제 제품에서는 파서 계층(hwp/pdf/office/이미지 OCR)이 추출한
        텍스트를 이 메서드에 넘기게 된다.
        """
        p = Path(path)
        text = p.read_text(encoding=encoding, errors="replace")
        return self.scan_text(text)

    # ------------------------------------------------------------------
    # 중복 스팬 정리
    # ------------------------------------------------------------------
    def _resolve_overlaps(self, findings: list[Finding]) -> list[Finding]:
        """원문에서 겹치는 검출은 더 신뢰도 높은/우선순위 높은 것만 남긴다.

        예: 13자리 숫자가 카드번호 패턴과 계좌 패턴에 동시에 잡힐 때
        검증된(VERIFIED) 카드번호를 우선한다.
        """
        kept: list[Finding] = []
        order = sorted(findings, key=lambda f: (f.start, -(f.end - f.start)))
        for f in order:
            conflict_idx = None
            for i, k in enumerate(kept):
                if f.start < k.end and k.start < f.end:  # 구간 겹침
                    conflict_idx = i
                    break
            if conflict_idx is None:
                kept.append(f)
            elif self._is_better(f, kept[conflict_idx]):
                kept[conflict_idx] = f
        return kept

    def _is_better(self, a: Finding, b: Finding) -> bool:
        """a가 b보다 우선(살아남아야)하면 True."""
        # 1) 검증된 항목 우선
        a_ver = a.confidence is Confidence.VERIFIED
        b_ver = b.confidence is Confidence.VERIFIED
        if a_ver != b_ver:
            return a_ver
        # 2) 등록 순서(낮은 rank = 높은 우선순위)
        ra, rb = self._rank.get(a.detector, 99), self._rank.get(b.detector, 99)
        if ra != rb:
            return ra < rb
        # 3) 더 긴 매치 우선
        return (a.end - a.start) > (b.end - b.start)

    # ------------------------------------------------------------------
    # 집계
    # ------------------------------------------------------------------
    def summarize(self, findings: list[Finding]) -> ScanSummary:
        by_severity: dict[str, int] = {}
        by_type: dict[str, int] = {}
        verified = pattern_only = 0
        for f in findings:
            by_severity[f.severity.value] = by_severity.get(f.severity.value, 0) + 1
            by_type[f.info_type] = by_type.get(f.info_type, 0) + 1
            if f.confidence is Confidence.VERIFIED:
                verified += 1
            else:
                pattern_only += 1
        return ScanSummary(
            total=len(findings),
            by_severity=by_severity,
            by_type=by_type,
            verified=verified,
            pattern_only=pattern_only,
        )
