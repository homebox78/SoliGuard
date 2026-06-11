"""검출 엔진 오케스트레이터.

여러 검출기를 등록하고, 텍스트/파일을 2단계로 스캔한 뒤,
화이트리스트 필터링과 중복 스팬 정리를 거쳐 Finding 목록을 돌려준다.

직무(role)별로 활성 검출기를 다르게 구성해 '직무별 스캔 프로파일'
(기획서 5장 차별점 #1)의 검출 엔진 측 기반을 제공한다.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable, Sequence

from .base import Confidence, Detector, Finding, LineIndex, Severity
from .detectors import DEFAULT_DETECTORS
from .whitelist import build_user_keys, is_dummy, norm_key

__all__ = ["DetectionEngine", "ScanSummary"]

# (시작, 끝, 라벨) — 구조화 포맷(표/JSON)에서 값이 속한 필드 구간
FieldSpan = tuple[int, int, str]

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
        roles: Iterable[str] | None = None,
        enabled_types: Iterable[str] | None = None,
        user_whitelist: Iterable[str] | None = None,
    ) -> None:
        """엔진 생성.

        :param detectors: 사용할 검출기 인스턴스(기본: DEFAULT_DETECTORS 전체)
        :param role: 단일 직무(하위호환). roles 와 합쳐진다.
        :param roles: 복수 직무. 선택한 직무들의 검출기 '합집합'을 활성화한다.
        :param enabled_types: 활성화할 검출기 name 집합(role/roles보다 우선)
        """
        if detectors is None:
            detectors = [cls() for cls in DEFAULT_DETECTORS]
        # 등록 순서 = 중복 스팬 우선순위
        self._all: list[Detector] = list(detectors)
        self._rank = {d.name: i for i, d in enumerate(self._all)}
        self._by_name = {d.name: d for d in self._all}
        self._user_wl: set[str] = build_user_keys(user_whitelist)

        role_set: set[str] = set(roles or ())
        if role:
            role_set.add(role)

        if enabled_types is not None:
            wanted = set(enabled_types)
            self._active = [d for d in self._all if d.name in wanted]
        elif role_set:
            self._active = [d for d in self._all if self._role_active(d, role_set)]
        else:
            self._active = list(self._all)

    @staticmethod
    def _role_active(detector: Detector, role_set: set[str]) -> bool:
        """공통 검출기(default_roles 비어 있음)는 항상, 특화 검출기는 선택 직무 중
        하나라도 일치하면 활성(복수 직무의 합집합)."""
        if not detector.default_roles:
            return True
        return bool(detector.default_roles & role_set)

    @property
    def active_detectors(self) -> list[str]:
        return [d.name for d in self._active]

    # ------------------------------------------------------------------
    # 스캔
    # ------------------------------------------------------------------
    def scan_text(
        self, text: str, fields: Sequence[FieldSpan] | None = None
    ) -> list[Finding]:
        """주어진 텍스트를 스캔해 정리된 Finding 목록을 반환.

        :param fields: 구조화 포맷(CSV/XLSX/JSON)에서 추출한 (시작,끝,필드라벨)
            구간 목록. 값이 속한 컬럼/키 라벨을 검출 결과에 부착하고,
            라벨이 유형과 일치하면 검증 실패 후보도 '필드 보강'으로 구제한다.
        """
        line_index = LineIndex.build(text)
        spans = sorted(fields or (), key=lambda s: (s[0], -(s[1] - s[0])))
        raw_findings: list[Finding] = []
        for det in self._active:
            for finding in det.detect(text, line_index):
                if is_dummy(finding.detector, finding.raw):
                    continue
                if self._user_wl and norm_key(finding.raw) in self._user_wl:
                    continue  # 사용자 지정 오탐 제외

                label = self._field_of(finding, spans)
                in_field = bool(label) and self._label_matches(det, label)

                if finding.weak:
                    # 형식만 일치한 후보: keep_unverified 거나, 소속 필드 라벨이
                    # 이 유형과 일치할 때만 보존(자유 텍스트 오탐은 차단).
                    if not (det.keep_unverified or in_field):
                        continue
                    if in_field:
                        # 라벨이 유형을 확증 → 강등됐던 위험도를 원복
                        finding = replace(finding, severity=det.severity)

                # 문맥 의존형 유형(여권/면허 등): 필드 라벨이 있으면 승격
                if in_field and det.field_severity is not None:
                    finding = replace(finding, severity=det.field_severity)

                if label:
                    finding = replace(finding, field=label)
                raw_findings.append(finding)

        resolved = self._resolve_overlaps(raw_findings)
        resolved.sort(
            key=lambda f: (_SEVERITY_ORDER[f.severity], f.line, f.start)
        )
        return self._sanitize_contexts(resolved)

    @staticmethod
    def _sanitize_contexts(findings: list[Finding]) -> list[Finding]:
        """각 Finding.context 안에 들어간 '다른 검출값'의 원문을 모두 마스킹한다.

        미리보기/리포트의 '검출 위치'는 주변 문맥을 보여주는데, 인접한 다른
        개인정보가 평문으로 새는 것을 막는다(화면설계서 #3: 항상 마스킹)."""
        pairs = sorted(
            {(f.raw, f.masked) for f in findings if f.raw},
            key=lambda p: len(p[0]), reverse=True,  # 긴 원문부터 치환(부분 겹침 방지)
        )
        out: list[Finding] = []
        for f in findings:
            ctx = f.context
            if ctx:
                for raw, masked in pairs:
                    if raw in ctx:
                        ctx = ctx.replace(raw, masked)
            out.append(replace(f, context=ctx) if ctx != f.context else f)
        return out

    @staticmethod
    def _field_of(finding: Finding, spans: Sequence[FieldSpan]) -> str:
        """검출 위치를 포함하는 가장 작은 필드 구간의 라벨(없으면 빈 문자열)."""
        for s, e, label in spans:
            if s <= finding.start and finding.end <= e:
                return label
        return ""

    @staticmethod
    def _label_matches(det: Detector, label: str) -> bool:
        """필드 라벨에 이 검출기의 키워드가 포함되면 True(대소문자·공백 무시)."""
        if not det.field_keywords:
            return False
        norm = label.lower().replace(" ", "").replace("_", "")
        return any(kw.lower().replace(" ", "") in norm for kw in det.field_keywords)

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
