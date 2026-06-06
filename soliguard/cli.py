"""SoliGuard 데모 CLI - 스캔→검출 파이프라인.

파일 또는 폴더를 스캔해 검출 결과와 위험 등급을 출력한다(조치/리포트 전 단계).
추출기(extractors)를 통해 txt/csv/xlsx/docx/hwpx/pdf/이미지 등을 처리하며,
파싱 실패 파일은 '검사불가'로 분리 표시한다.

사용 예:
    py -m soliguard.cli 스캔할_폴더 --role developer
    py -m soliguard.cli sample.txt --no-ocr
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .detection import DetectionEngine, Severity
from .detection.detectors import (
    ROLE_DESIGNER,
    ROLE_DEVELOPER,
    ROLE_FINANCE,
    ROLE_PLANNER,
    ROLE_PM,
)
from .scanner import scan_paths

_GRADE_ICON = {"위험": "🔴", "주의": "🟡", "안전": "🟢"}
_SEV_ICON = {Severity.HIGH: "🔴", Severity.MEDIUM: "🟡", Severity.LOW: "🟢"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="soliguard",
        description="SoliGuard 검출 엔진 PoC - 파일/폴더에서 개인정보를 검출합니다.",
    )
    parser.add_argument("target", help="스캔할 파일 또는 폴더 경로")
    parser.add_argument(
        "--role",
        choices=[
            ROLE_DEVELOPER, ROLE_DESIGNER, ROLE_PLANNER, ROLE_PM, ROLE_FINANCE,
        ],
        default=None,
        help="직무 프로파일(미지정 시 전체 검출기 활성화)",
    )
    parser.add_argument(
        "--show-context", action="store_true",
        help="검출 위치 주변 문맥 표시(마스킹 안 됨, 디버깅용)",
    )
    parser.add_argument(
        "--no-ocr", action="store_true",
        help="이미지/스캔 PDF OCR 비활성화(기본은 로컬 OCR 활성)",
    )
    parser.add_argument(
        "--report", metavar="PATH",
        help="PDF 진단 리포트 저장 경로(reportlab 필요)",
    )
    args = parser.parse_args(argv)

    target = Path(args.target)
    if not target.exists():
        print(f"경로를 찾을 수 없습니다: {target}", file=sys.stderr)
        return 2

    engine = DetectionEngine(role=args.role)
    print(f"활성 검출기: {', '.join(engine.active_detectors)}")
    print(f"스캔 대상: {target}\n")

    file_results = list(scan_paths([target], engine, ocr_enabled=not args.no_ocr))

    all_findings: list[tuple[Path, object]] = []
    unreadable: list[tuple[Path, str]] = []
    scanned = len(file_results)
    for result in file_results:
        if result.status == "검사불가":
            unreadable.append((result.path, result.error))
            continue
        for f in result.findings:
            all_findings.append((result.path, f))

    # 결과 출력
    if not all_findings:
        print(f"검사한 파일 {scanned}개 — 검출된 개인정보가 없습니다. 🟢 안전")
    else:
        print(f"{'위험도':<6}{'유형':<14}{'신뢰도':<8}{'위치':<28}미리보기")
        print("-" * 90)
        for fpath, f in all_findings:
            loc = f"{fpath.name}:{f.line}"
            icon = _SEV_ICON[f.severity]
            print(
                f"{icon}{f.severity.value:<5}{f.info_type:<14}"
                f"{f.confidence.value:<8}{loc:<28}{f.masked}"
            )
            if args.show_context and f.context:
                print(f"        ↳ {f.context}")
        print("-" * 90)

    if unreadable:
        print(f"\n검사불가 {len(unreadable)}건:")
        for p, err in unreadable:
            print(f"  · {p.name} — {err}")

    summary = engine.summarize([f for _, f in all_findings])
    grade = summary.risk_grade()
    print(
        f"\n검사 파일 {scanned}개 / 검출 {summary.total}건 "
        f"(검증됨 {summary.verified}, 패턴일치 {summary.pattern_only})"
    )
    if summary.by_type:
        print("유형별:", ", ".join(f"{k} {v}" for k, v in summary.by_type.items()))
    print(f"PC 위험 등급: {_GRADE_ICON.get(grade, '')} {grade}")

    if args.report:
        from .report import ReportError, generate_pdf_report

        try:
            out = generate_pdf_report(file_results, args.role, Path(args.report))
            print(f"\n📑 진단 리포트 저장: {out}")
        except ReportError as exc:
            print(f"\n리포트 생성 실패: {exc}", file=sys.stderr)
            return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
