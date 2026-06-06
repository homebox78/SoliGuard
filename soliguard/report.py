"""PDF 진단 리포트 생성 - 발주처 보안 감사·법규 대응 증빙용.

reportlab 으로 생성하며, 개인정보가 리포트에 노출되지 않도록 마스킹된 값(f.masked)만
싣는다. 리포트 자체가 새로운 유출 경로가 되지 않게 하는 것이 핵심 설계다.

입력은 scanner.FileScanResult 리스트(또는 engine.run_scan 의 ScanSummary)다.
reportlab 미설치 시 ReportError 로 명확히 안내한다(핵심 엔진은 reportlab 불필요).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Sequence

from .detection import Severity

__all__ = ["generate_pdf_report", "ReportError", "ReportSummary", "summarize_results"]


class ReportError(Exception):
    """리포트 생성 불가(reportlab 미설치 등)."""


@dataclass
class ReportSummary:
    """리포트/대시보드 공용 집계."""

    scanned: int            # 검사 완료 파일 수
    skipped: int            # 검사불가 파일 수
    total_findings: int
    by_severity: dict[str, int]   # {"높음": n, "중간": n, "낮음": n}

    @property
    def risk_grade(self) -> str:
        if self.by_severity.get(Severity.HIGH.value, 0) > 0:
            return "위험"
        if self.total_findings > 0:
            return "주의"
        return "안전"


def summarize_results(file_results: Sequence) -> ReportSummary:
    """FileScanResult 리스트를 집계해 ReportSummary 를 만든다."""
    scanned = skipped = 0
    by_severity: dict[str, int] = {}
    total = 0
    for r in file_results:
        if getattr(r, "status", "") == "검사불가":
            skipped += 1
            continue
        scanned += 1
        for f in r.findings:
            by_severity[f.severity.value] = by_severity.get(f.severity.value, 0) + 1
            total += 1
    return ReportSummary(scanned, skipped, total, by_severity)


# 폰트/색 상수 -------------------------------------------------------------
_GRADE_COLOR = {"안전": "#16A34A", "주의": "#D97706", "위험": "#DC2626"}
_SEV_COLOR = {
    Severity.HIGH: "#DC2626",
    Severity.MEDIUM: "#D97706",
    Severity.LOW: "#16A34A",
}
import os as _os

_FONT_CANDIDATES = [
    # Pretendard 우선(앱 전체 폰트 통일). 시스템/사용자 설치 경로 모두 탐색.
    "C:/Windows/Fonts/Pretendard-Regular.ttf",
    _os.path.expandvars(
        r"%LOCALAPPDATA%/Microsoft/Windows/Fonts/Pretendard-Regular.ttf"),
    "/usr/share/fonts/truetype/pretendard/Pretendard-Regular.ttf",
    # 폴백
    "C:/Windows/Fonts/malgun.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
]


def _register_font() -> str:
    """한글 폰트 등록. 실패 시 Helvetica 폴백(한글 깨질 수 있음)."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    for path in _FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("KR", path))
                return "KR"
            except Exception:
                continue
    return "Helvetica"


def generate_pdf_report(
    results_or_summary,
    profile: str | None,
    output_path: str | Path,
    project_name: str = "",
) -> Path:
    """진단 리포트 PDF를 생성하고 저장 경로를 반환.

    results_or_summary 는 FileScanResult 리스트 또는 .file_results 를 가진
    ScanSummary(engine.run_scan 결과) 둘 다 받는다(문서 스펙 호환)."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
    except ImportError as e:
        raise ReportError(
            "PDF 리포트 생성에 reportlab 이 필요합니다 (pip install reportlab)"
        ) from e

    # ScanSummary(.file_results) 또는 리스트 모두 허용
    file_results = getattr(results_or_summary, "file_results", results_or_summary)
    output_path = Path(output_path)
    summary = summarize_results(file_results)
    font = _register_font()

    c = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4

    # ── 헤더 ── (Solideo 크림슨)
    c.setFillColor(colors.HexColor("#C8174E"))
    c.rect(0, height - 22 * mm, width, 22 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont(font, 18)
    c.drawString(20 * mm, height - 15 * mm, "SoliGuard 개인정보 점검 진단서")

    y = height - 30 * mm

    # ── 메타 정보 ──
    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont(font, 10)
    meta = [
        f"점검 일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"점검자: {os.getenv('USERNAME') or os.getenv('USER') or '-'}"
        f"    직무 프로파일: {profile or '-'}",
        f"프로젝트: {project_name or '-'}",
        f"검사 파일: {summary.scanned}개    검사불가: {summary.skipped}개",
    ]
    for line in meta:
        c.drawString(20 * mm, y, line)
        y -= 6 * mm
    y -= 4 * mm

    # ── 종합 위험 등급 ──
    grade = summary.risk_grade
    c.setFillColor(colors.HexColor(_GRADE_COLOR[grade]))
    c.setFont(font, 14)
    c.drawString(
        20 * mm, y, f"종합 위험 등급: {grade}  (총 {summary.total_findings}건 발견)"
    )
    y -= 8 * mm

    # ── 위험도별 요약 ──
    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont(font, 10)
    sev = summary.by_severity
    c.drawString(
        20 * mm,
        y,
        f"높음 {sev.get('높음', 0)}건  /  중간 {sev.get('중간', 0)}건  /  "
        f"낮음 {sev.get('낮음', 0)}건",
    )
    y -= 10 * mm

    # ── 상세 목록 (마스킹된 값만 기재) ──
    c.setFont(font, 11)
    c.drawString(20 * mm, y, "검출 상세 (개인정보는 마스킹되어 표시됩니다)")
    y -= 7 * mm
    c.setFont(font, 8)

    def _page_break_if_needed(threshold: float) -> None:
        nonlocal y
        if y < threshold * mm:
            c.showPage()
            y = height - 30 * mm
            c.setFont(font, 8)

    for r in file_results:
        findings = getattr(r, "findings", [])
        if not findings:
            continue
        _page_break_if_needed(30)
        c.setFillColor(colors.HexColor("#0F172A"))
        c.drawString(20 * mm, y, f"[파일] {r.path}  ({len(findings)}건)")
        y -= 5 * mm
        for f in findings:
            _page_break_if_needed(25)
            c.setFillColor(colors.HexColor(_SEV_COLOR.get(f.severity, "#000000")))
            c.drawString(
                25 * mm,
                y,
                f"[{f.severity.value}] {f.info_type}: {f.masked}  (line {f.line})",
            )
            y -= 4.5 * mm
        y -= 2 * mm

    # ── 검사불가 목록 ──
    unreadable = [r for r in file_results if getattr(r, "status", "") == "검사불가"]
    if unreadable:
        _page_break_if_needed(30)
        c.setFillColor(colors.HexColor("#64748B"))
        c.setFont(font, 10)
        c.drawString(20 * mm, y, f"검사불가 {len(unreadable)}건")
        y -= 6 * mm
        c.setFont(font, 8)
        for r in unreadable:
            _page_break_if_needed(25)
            c.drawString(25 * mm, y, f"· {r.path} — {r.error}")
            y -= 4.5 * mm

    # ── 푸터(법적 근거 안내) ──
    c.showPage()
    c.setFont(font, 9)
    c.setFillColor(colors.HexColor("#64748B"))
    footer = [
        "※ 본 진단서는 개인정보보호법 제21조(파기), 제24조(고유식별정보 처리 제한),",
        "   제29조(안전조치의무) 이행 점검 및 발주처 보안 감사 증빙용으로 활용될 수 있습니다.",
        "※ 본 점검은 사용자 PC 내에서 수행되었으며, 검출된 데이터는 외부로 전송되지 않았습니다.",
        "※ 모든 조치 내역은 감사 로그(audit.log)에 별도 기록됩니다.",
    ]
    fy = height - 30 * mm
    for line in footer:
        c.drawString(20 * mm, fy, line)
        fy -= 6 * mm

    c.save()
    return output_path
