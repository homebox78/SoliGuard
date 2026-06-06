"""engine.run_scan 오케스트레이션 파사드 테스트."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

from soliguard.engine import ScanSummary, run_scan

HAS_REPORTLAB = importlib.util.find_spec("reportlab") is not None


class TestRunScan(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        (self.dir / "leak.txt").write_text(
            "홍길동 900101-1234568 카드 4242424242424242", encoding="utf-8"
        )
        (self.dir / "broken.pdf").write_bytes(b"not a pdf")
        (self.dir / "app.py").write_text(
            'api_key = "aZ9kQ2mB7xL1pR4tWvN3sT6u"', encoding="utf-8"
        )

    def test_counts_and_grade(self):
        s = run_scan([self.dir], role="developer")
        self.assertIsInstance(s, ScanSummary)
        self.assertEqual(s.skipped, 1)              # broken.pdf
        self.assertEqual(s.scanned, 2)              # leak.txt + app.py
        self.assertGreaterEqual(s.total_findings, 3)
        self.assertEqual(s.risk_grade, "위험")
        self.assertEqual(s.risk_grade_key, "danger")

    def test_profile_developer_finds_secret(self):
        s = run_scan([self.dir], profile="개발자")
        kinds = {f.info_type for f in s.all_findings()}
        self.assertIn("API 키/시크릿", kinds)

    def test_profile_planner_excludes_secret(self):
        s = run_scan([self.dir], profile="기획자")
        kinds = {f.info_type for f in s.all_findings()}
        self.assertNotIn("API 키/시크릿", kinds)

    def test_user_whitelist_excludes(self):
        # 카드번호를 사용자 오탐으로 등록 → 다음 스캔에서 제외(구분자 무관)
        base = run_scan([self.dir], role="developer")
        self.assertIn("신용카드번호", {f.info_type for f in base.all_findings()})
        wl = run_scan([self.dir], role="developer",
                      user_whitelist=["4242-4242-4242-4242"])
        self.assertNotIn("신용카드번호", {f.info_type for f in wl.all_findings()})

    def test_multiple_profiles_union(self):
        # 기획자(시크릿 제외) + 개발자(시크릿 포함) 복수 선택 → 합집합으로 시크릿 검출
        s = run_scan([self.dir], profiles=["기획자", "개발자"])
        kinds = {f.info_type for f in s.all_findings()}
        self.assertIn("API 키/시크릿", kinds)

    def test_progress_and_stop(self):
        seen = []
        run_scan([self.dir], role="developer",
                 progress_cb=lambda i, t, p: seen.append((i, t)))
        self.assertTrue(seen)
        self.assertEqual(seen[-1][0], seen[-1][1])  # 마지막 done == total

        # should_stop=True 면 즉시 중단 → 결과 없음
        stopped = run_scan([self.dir], role="developer", should_stop=lambda: True)
        self.assertEqual(stopped.scanned + stopped.skipped, 0)

    @unittest.skipUnless(HAS_REPORTLAB, "reportlab 미설치")
    def test_report_accepts_scan_summary(self):
        from soliguard.report import generate_pdf_report

        s = run_scan([self.dir], role="developer")
        out = self.dir / "r.pdf"
        generate_pdf_report(s, "개발자", out)   # ScanSummary 직접 전달(문서 스펙)
        self.assertTrue(out.read_bytes().startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
