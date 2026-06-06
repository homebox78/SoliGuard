"""조치 계층 테스트: 마스킹 / 격리·복원 / 안전 삭제 / 감사 로그."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from soliguard import actions
from soliguard.detection import DetectionEngine

HAS_CRYPTO = importlib.util.find_spec("cryptography") is not None

SAMPLE = '고객 홍길동 900101-1234568 카드 4242424242424242\napi_key = "aZ9kQ2mB7xL1pR4tWvN3"\n'


class ActionTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        # 모듈 전역 저장 위치를 임시 폴더로 격리
        actions.SOLIGUARD_HOME = self.dir / ".soliguard"
        actions.QUARANTINE_DIR = actions.SOLIGUARD_HOME / "quarantine"
        actions.AUDIT_LOG = actions.SOLIGUARD_HOME / "audit.log"
        self.engine = DetectionEngine()

    def _sample_file(self) -> Path:
        p = self.dir / "leak.txt"
        p.write_text(SAMPLE, encoding="utf-8")
        return p


class TestMasking(ActionTestBase):
    def test_mask_creates_copy_with_no_raw(self):
        p = self._sample_file()
        findings = self.engine.scan_text(SAMPLE)
        result = actions.mask_in_text_file(p, findings)
        self.assertEqual(result.status, "success")

        out = Path(result.detail)
        self.assertTrue(out.exists())
        masked_text = out.read_text(encoding="utf-8")
        self.assertNotIn("900101-1234568", masked_text)
        self.assertNotIn("4242424242424242", masked_text)
        self.assertNotIn("aZ9kQ2mB7xL1pR4tWvN3", masked_text)
        # 원본은 보존
        self.assertIn("900101-1234568", p.read_text(encoding="utf-8"))

    def test_audit_written(self):
        p = self._sample_file()
        findings = self.engine.scan_text(SAMPLE)
        actions.mask_in_text_file(p, findings)
        lines = actions.AUDIT_LOG.read_text(encoding="utf-8").strip().splitlines()
        rec = json.loads(lines[-1])
        self.assertEqual(rec["action"], "mask")
        self.assertEqual(rec["result"], "success")


class TestSecureDelete(ActionTestBase):
    def test_requires_confirmation(self):
        p = self._sample_file()
        result = actions.secure_delete(p, confirmed=False)
        self.assertEqual(result.status, "failed")
        self.assertTrue(p.exists())  # 확인 없으면 삭제 안 됨

    def test_deletes_when_confirmed(self):
        p = self._sample_file()
        result = actions.secure_delete(p, confirmed=True)
        self.assertEqual(result.status, "success")
        self.assertFalse(p.exists())


@unittest.skipUnless(HAS_CRYPTO, "cryptography 미설치")
class TestQuarantine(ActionTestBase):
    def test_quarantine_and_restore(self):
        p = self._sample_file()
        original = p.read_bytes()

        q = actions.quarantine_file(p)
        self.assertEqual(q.status, "success")
        self.assertFalse(p.exists())  # 원본 제거됨
        qid = q.detail
        self.assertTrue((actions.QUARANTINE_DIR / f"{qid}.enc").exists())

        r = actions.restore_file(qid)
        self.assertEqual(r.status, "success")
        self.assertTrue(p.exists())
        self.assertEqual(p.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
