"""스캔 오케스트레이션: 파일/폴더 → 텍스트 추출 → 검출 엔진 적용.

MVP 백엔드 파이프라인의 '스캔 → 검출' 구간. 한 파일의 파싱 실패가 전체
스캔을 멈추지 않도록 '검사불가'로 분리 기록한다(기획서 9장 리스크 #3).
조치 단계는 actions.py 가 담당한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from .detection import DetectionEngine, Finding, Severity
from .extractors import ExtractionError, extract_doc, is_supported

__all__ = [
    "FileScanResult",
    "scan_file",
    "scan_paths",
    "collect_files",
    "Scanner",
]


@dataclass
class FileScanResult:
    path: Path
    status: str                      # "완료" | "검사불가"
    findings: list[Finding] = field(default_factory=list)
    error: str = ""

    @property
    def count(self) -> int:
        return len(self.findings)

    @property
    def top_severity(self):
        """이 파일에서 가장 높은 위험도(없으면 None)."""
        if not self.findings:
            return None
        order = {Severity.HIGH: 3, Severity.MEDIUM: 2, Severity.LOW: 1}
        return max(self.findings, key=lambda f: order[f.severity]).severity


def scan_file(
    path: str | Path, engine: DetectionEngine, ocr_enabled: bool = True
) -> FileScanResult:
    """파일 1개를 추출→검출. 추출 실패 시 status='검사불가'."""
    path = Path(path)
    try:
        doc = extract_doc(path, ocr_enabled=ocr_enabled)
    except ExtractionError as e:
        return FileScanResult(path, "검사불가", error=str(e))
    findings = engine.scan_text(doc.text, fields=doc.fields)
    return FileScanResult(path, "완료", findings=findings)


def collect_files(
    targets: list[str | Path], exclude: set[str] | None = None
) -> list[Path]:
    """대상(파일/폴더)에서 지원 포맷 파일 경로를 수집한다.

    GUI가 진행률(N/M)을 표시하려면 전체 파일 수를 먼저 알아야 하므로
    스캔과 분리해 제공한다.
    """
    exclude = exclude or set()
    out: list[Path] = []
    for target in targets:
        target = Path(target)
        if target.is_file():
            candidates = [target]
        elif target.is_dir():
            candidates = [p for p in target.rglob("*") if p.is_file()]
        else:
            candidates = []
        for fpath in candidates:
            if any(part in exclude for part in fpath.parts):
                continue
            if is_supported(fpath):
                out.append(fpath)
    return out


def scan_paths(
    targets: list[str | Path],
    engine: DetectionEngine,
    ocr_enabled: bool = True,
    exclude: set[str] | None = None,
) -> Iterator[FileScanResult]:
    """파일/폴더 목록을 순회하며 결과를 하나씩 yield.

    GUI 진행률 표시와 이어지도록 제너레이터로 흘려보낸다(화면설계서: 스캔 진행).
    """
    for fpath in collect_files(targets, exclude):
        yield scan_file(fpath, engine, ocr_enabled=ocr_enabled)


class Scanner:
    """진행 상황 집계가 필요한 호출자를 위한 얇은 래퍼."""

    def __init__(self, engine: DetectionEngine, ocr_enabled: bool = True) -> None:
        self.engine = engine
        self.ocr_enabled = ocr_enabled
        self.results: list[FileScanResult] = []

    def run(
        self, targets: list[str | Path], exclude: set[str] | None = None
    ) -> list[FileScanResult]:
        self.results = list(
            scan_paths(targets, self.engine, self.ocr_enabled, exclude)
        )
        return self.results

    def all_findings(self) -> list[Finding]:
        out: list[Finding] = []
        for r in self.results:
            out.extend(r.findings)
        return out
