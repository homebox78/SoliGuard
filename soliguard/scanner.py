"""스캔 오케스트레이션: 파일/폴더 → 텍스트 추출 → 검출 엔진 적용.

MVP 백엔드 파이프라인의 '스캔 → 검출' 구간. 한 파일의 파싱 실패가 전체
스캔을 멈추지 않도록 '검사불가'로 분리 기록한다(기획서 9장 리스크 #3).
조치 단계는 actions.py 가 담당한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from .detection import DetectionEngine, Finding
from .extractors import ExtractionError, extract_text, is_supported

__all__ = ["FileScanResult", "scan_file", "scan_paths", "Scanner"]


@dataclass
class FileScanResult:
    path: Path
    status: str                      # "완료" | "검사불가"
    findings: list[Finding] = field(default_factory=list)
    error: str = ""

    @property
    def count(self) -> int:
        return len(self.findings)


def scan_file(
    path: str | Path, engine: DetectionEngine, ocr_enabled: bool = True
) -> FileScanResult:
    """파일 1개를 추출→검출. 추출 실패 시 status='검사불가'."""
    path = Path(path)
    try:
        text = extract_text(path, ocr_enabled=ocr_enabled)
    except ExtractionError as e:
        return FileScanResult(path, "검사불가", error=str(e))
    findings = engine.scan_text(text)
    return FileScanResult(path, "완료", findings=findings)


def scan_paths(
    targets: list[str | Path],
    engine: DetectionEngine,
    ocr_enabled: bool = True,
    exclude: set[str] | None = None,
) -> Iterator[FileScanResult]:
    """파일/폴더 목록을 순회하며 결과를 하나씩 yield.

    GUI 진행률 표시와 이어지도록 제너레이터로 흘려보낸다(화면설계서: 스캔 진행).
    """
    exclude = exclude or set()
    for target in targets:
        target = Path(target)
        if target.is_file():
            files = [target]
        else:
            files = [p for p in target.rglob("*") if p.is_file()]
        for fpath in files:
            if any(part in exclude for part in fpath.parts):
                continue
            if not is_supported(fpath):
                continue
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
