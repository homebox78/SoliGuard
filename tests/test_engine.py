"""검출 엔진 통합 테스트."""

import unittest

from soliguard.detection import Confidence, DetectionEngine, Severity
from soliguard.detection.detectors import ROLE_DEVELOPER, ROLE_PLANNER

SAMPLE = """\
고객 홍길동 주민번호 900101-1234568 입니다.
잘못된 주민번호 900101-1234567 은 검출되면 안 됨(체크섬 불일치).
결제 카드 4242 4242 4242 4242 사용.
사업자등록번호 123-45-67891.
연락처 010-1234-5678, 이메일 hong@example.com.
테스트 카드 4111-1111-1111-1111 은 더미라 제외.

# config.py
api_key = "aZ9kQ2mB7xL1pR4tWvN3"
password = "password"
db = "mysql://admin:s3cr3tPw@10.0.0.5:3306/customers"
"""


class TestEngineFullScan(unittest.TestCase):
    def setUp(self):
        self.engine = DetectionEngine(role=ROLE_DEVELOPER)
        self.findings = self.engine.scan_text(SAMPLE)
        self.by_detector = {}
        for f in self.findings:
            self.by_detector.setdefault(f.detector, []).append(f)

    def test_valid_rrn_detected_once(self):
        rrns = self.by_detector.get("rrn", [])
        self.assertEqual(len(rrns), 1, f"기대 1건, 실제 {len(rrns)}건")
        self.assertEqual(rrns[0].confidence, Confidence.VERIFIED)
        self.assertEqual(rrns[0].severity, Severity.HIGH)

    def test_rrn_masked_in_output(self):
        rrn = self.by_detector["rrn"][0]
        self.assertNotIn("1234568", rrn.masked)
        self.assertTrue(rrn.masked.startswith("90****"))

    def test_credit_card_detected(self):
        cards = self.by_detector.get("credit_card", [])
        self.assertEqual(len(cards), 1)  # 더미 4111... 은 제외됨
        self.assertTrue(cards[0].masked.endswith("4242"))

    def test_brn_detected(self):
        self.assertEqual(len(self.by_detector.get("brn", [])), 1)

    def test_phone_and_email(self):
        self.assertEqual(len(self.by_detector.get("phone", [])), 1)
        self.assertEqual(len(self.by_detector.get("email", [])), 1)

    def test_secret_detected(self):
        secrets = self.by_detector.get("secret", [])
        types = {f.info_type for f in secrets}
        self.assertIn("API 키/시크릿", types)
        self.assertIn("DB 접속정보", types)

    def test_weak_password_pattern_only(self):
        # 'password = "password"' 는 엔트로피 낮아 PATTERN_ONLY
        weak = [
            f for f in self.by_detector.get("secret", [])
            if f.confidence is Confidence.PATTERN_ONLY
        ]
        self.assertTrue(weak, "약한 비밀번호가 PATTERN_ONLY로 잡혀야 함")

    def test_secret_value_masked(self):
        for f in self.by_detector.get("secret", []):
            self.assertNotIn("aZ9kQ2mB7xL1pR4tWvN3", f.masked)


class TestRoleProfiles(unittest.TestCase):
    def test_planner_excludes_secret(self):
        engine = DetectionEngine(role=ROLE_PLANNER)
        self.assertNotIn("secret", engine.active_detectors)
        self.assertIn("rrn", engine.active_detectors)

    def test_developer_includes_secret(self):
        engine = DetectionEngine(role=ROLE_DEVELOPER)
        self.assertIn("secret", engine.active_detectors)


class TestSummary(unittest.TestCase):
    def test_risk_grade(self):
        engine = DetectionEngine(role=ROLE_DEVELOPER)
        findings = engine.scan_text(SAMPLE)
        summary = engine.summarize(findings)
        self.assertEqual(summary.risk_grade(), "위험")  # HIGH 항목 존재
        self.assertGreater(summary.verified, 0)

    def test_clean_text_safe(self):
        engine = DetectionEngine()
        findings = engine.scan_text("오늘 날씨가 참 좋습니다. 회의는 3시입니다.")
        self.assertEqual(engine.summarize(findings).risk_grade(), "안전")


if __name__ == "__main__":
    unittest.main()
