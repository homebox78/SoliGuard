"""스캔 오케스트레이션 파사드 - run_scan(folders, ...) → ScanSummary.

설계 문서(앱골격·스케줄러·GUI)가 공통으로 참조하는 상위 진입점이다.
내부적으로는 detection 패키지의 DetectionEngine + scanner + report 집계를 조합한다.

문서 스펙과의 매핑:
    문서의 soliguard.engine.run_scan / ScanSummary / FileResult  ≡  본 모듈
    문서의 soliguard.detectors (평면)                            ≡  soliguard.detection 패키지
    문서의 Finding.kind                                          ≡  Finding.info_type
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .detection import DetectionEngine, Finding, Severity
from .detection.detectors import (
    ROLE_DESIGNER, ROLE_DEVELOPER, ROLE_FINANCE, ROLE_PM, ROLE_PLANNER,
)
from .report import ReportSummary, summarize_results
from .scanner import FileScanResult, collect_files, scan_file

__all__ = ["run_scan", "ScanSummary", "FileResult", "DEFAULT_EXCLUDES", "PROFILE_ROLE"]

# 화면 표시 직무명(한국어) → 엔진 role
PROFILE_ROLE = {
    "개발자": ROLE_DEVELOPER,
    "디자이너": ROLE_DESIGNER,
    "기획자": ROLE_PLANNER,
    "PM": ROLE_PM,
    "전산사무": ROLE_FINANCE,
}

# 스캔에서 기본 제외할 폴더(성능·노이즈 방지)
DEFAULT_EXCLUDES = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    ".soliguard", "Windows", "Program Files", "Program Files (x86)",
}

# 문서 스펙의 FileResult ≡ scanner.FileScanResult (동일 객체를 별칭으로 노출)
FileResult = FileScanResult


@dataclass
class ScanSummary:
    """스캔 전체 집계. 문서 스펙의 ScanSummary 인터페이스를 제공한다."""

    file_results: list[FileScanResult] = field(default_factory=list)
    scanned: int = 0
    skipped: int = 0

    @property
    def _agg(self) -> ReportSummary:
        return summarize_results(self.file_results)

    @property
    def total_findings(self) -> int:
        return self._agg.total_findings

    @property
    def by_severity(self) -> dict[str, int]:
        return self._agg.by_severity

    @property
    def risk_grade(self) -> str:
        """위험 등급(한국어 정규값): '위험' | '주의' | '안전'."""
        return self._agg.risk_grade

    @property
    def risk_grade_key(self) -> str:
        """영문 키: 'danger' | 'warn' | 'safe' (테마/아이콘 매핑용)."""
        return {"위험": "danger", "주의": "warn", "안전": "safe"}[self.risk_grade]

    def all_findings(self) -> list[Finding]:
        return [f for r in self.file_results for f in r.findings]


def run_scan(
    folders: list[str | Path],
    role: str | None = None,
    profile: str | None = None,
    roles: "list[str] | None" = None,
    profiles: "list[str] | None" = None,
    ocr_enabled: bool = True,
    excludes: set[str] | None = None,
    progress_cb: Callable[[int, int, str], None] | None = None,
    should_stop: Callable[[], bool] | None = None,
) -> ScanSummary:
    """폴더(들)를 스캔해 집계 결과를 반환.

    직무는 복수 지정 가능하며, 선택한 직무들의 검출기 '합집합'으로 검사한다.

    :param role/roles: 엔진 role(developer 등) 단일/복수.
    :param profile/profiles: 직무명(한국어, '개발자' 등) 단일/복수 → role로 매핑.
    :param progress_cb: progress_cb(done, total, current_path) 진행 보고.
    :param should_stop: True 반환 시 중지(부분 결과 반환).
    """
    role_set: set[str] = set(roles or ())
    if role:
        role_set.add(role)
    for p in list(profiles or []) + ([profile] if profile else []):
        r = PROFILE_ROLE.get(p)
        if r:
            role_set.add(r)
    excludes = (excludes or set()) | DEFAULT_EXCLUDES

    engine = DetectionEngine(roles=role_set or None)
    files = collect_files(folders, exclude=excludes)
    total = len(files)

    summary = ScanSummary()
    for i, path in enumerate(files, 1):
        if should_stop and should_stop():
            break
        if progress_cb:
            progress_cb(i, total, str(path))
        result = scan_file(path, engine, ocr_enabled=ocr_enabled)
        summary.file_results.append(result)
        if result.status == "검사불가":
            summary.skipped += 1
        else:
            summary.scanned += 1
    return summary
