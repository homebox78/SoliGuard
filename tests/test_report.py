"""PDF 리포트 생성 테스트."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

from soliguard.detection import DetectionEngine, Severity
from soliguard.report import ReportSummary, summarize_results
from soliguard.scanner import scan_file

HAS_REPORTLAB = importlib.util.find_spec("reportlab") is not None


def _make_results(dir_path: Path):
    leak = dir_path / "leak.txt"
    leak.write_text(
        "홍길동 900101-1234568 카드 4242424242424242", encoding="utf-8"
    )
    bad = dir_path / "broken.pdf"
    bad.write_bytes(b"not a pdf")
    engine = DetectionEngine()
    return [scan_file(leak, engine), scan_file(bad, engine)]


class TestSummarize(unittest.TestCase):
    def test_summary_counts_and_grade(self):
        with tempfile.TemporaryDirectory() as d:
            results = _make_results(Path(d))
            summary = summarize_results(results)
            self.assertEqual(summary.scanned, 1)
            self.assertEqual(summary.skipped, 1)   # broken.pdf
            self.assertGreaterEqual(summary.by_severity.get(Severity.HIGH.value, 0), 1)
            self.assertEqual(summary.risk_grade, "위험")

    def test_empty_is_safe(self):
        summary = ReportSummary(0, 0, 0, {})
        self.assertEqual(summary.risk_grade, "안전")


@unittest.skipUnless(HAS_REPORTLAB, "reportlab 미설치")
class TestPdfGeneration(unittest.TestCase):
    def test_generates_valid_pdf(self):
        from soliguard.report import generate_pdf_report

        with tempfile.TemporaryDirectory() as d:
            results = _make_results(Path(d))
            out = Path(d) / "report.pdf"
            generate_pdf_report(results, "developer", out)
            self.assertTrue(out.exists())
            data = out.read_bytes()
            self.assertTrue(data.startswith(b"%PDF"))
            self.assertGreater(len(data), 1000)


if __name__ == "__main__":
    unittest.main()
