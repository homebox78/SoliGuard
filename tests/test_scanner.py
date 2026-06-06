"""스캐너 오케스트레이션 테스트: 폴더 순회 + 검사불가 격리."""

import tempfile
import unittest
from pathlib import Path

from soliguard.detection import DetectionEngine
from soliguard.scanner import scan_file, scan_paths


class TestScanner(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.engine = DetectionEngine()

    def test_scan_text_file(self):
        p = self.dir / "a.txt"
        p.write_text("주민번호 900101-1234568", encoding="utf-8")
        result = scan_file(p, self.engine)
        self.assertEqual(result.status, "완료")
        self.assertEqual(result.count, 1)

    def test_corrupt_pdf_is_unreadable(self):
        # 실제 PDF가 아닌 파일 → 추출 실패 → 검사불가
        p = self.dir / "fake.pdf"
        p.write_bytes(b"not a real pdf")
        result = scan_file(p, self.engine)
        self.assertEqual(result.status, "검사불가")
        self.assertTrue(result.error)

    def test_scan_paths_skips_unsupported_and_collects(self):
        (self.dir / "a.txt").write_text("카드 4242424242424242", encoding="utf-8")
        (self.dir / "b.unknownext").write_text("무시됨", encoding="utf-8")
        (self.dir / "fake.pdf").write_bytes(b"broken")

        results = list(scan_paths([self.dir], self.engine))
        statuses = sorted(r.status for r in results)
        # a.txt(완료) + fake.pdf(검사불가). b.unknownext는 미지원이라 제외.
        self.assertEqual(statuses, ["검사불가", "완료"])
        completed = [r for r in results if r.status == "완료"]
        self.assertEqual(sum(r.count for r in completed), 1)


if __name__ == "__main__":
    unittest.main()
