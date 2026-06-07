"""확장자별 구조 인식 검증 고도화 테스트.

- 신규 검출기(여권/운전면허/IP/주소/외국인등록번호)
- 구조화 필드 라벨(컬럼 헤더) 기반 검증 실패 후보 '구제'
- CSV → 추출 → 검출 통합 경로
"""

import csv
import tempfile
import unittest
from pathlib import Path

from soliguard.detection import Confidence, DetectionEngine, Severity
from soliguard.detection.detectors import ROLE_DEVELOPER
from soliguard.detection import validators as V
from soliguard.extractors import extract_doc
from soliguard.scanner import scan_file


class TestNewValidators(unittest.TestCase):
    def test_passport(self):
        self.assertTrue(V.validate_passport("M12345678"))
        self.assertTrue(V.validate_passport("S87654321"))
        self.assertFalse(V.validate_passport("Z12345678"))   # 한국 발급기호 아님
        self.assertFalse(V.validate_passport("M11111111"))   # 전부 동일
        self.assertFalse(V.validate_passport("M1234567"))    # 자릿수 부족

    def test_driver_license(self):
        self.assertTrue(V.validate_driver_license("11-23-456789-01"))
        self.assertFalse(V.validate_driver_license("99-23-456789-01"))  # 지역코드 무효
        self.assertFalse(V.validate_driver_license("11-23-4567-01"))    # 자릿수

    def test_ipv4(self):
        self.assertTrue(V.valid_ipv4("192.168.0.10"))
        self.assertFalse(V.valid_ipv4("256.1.1.1"))
        self.assertFalse(V.valid_ipv4("10.01.0.1"))   # 선행 0
        self.assertFalse(V.valid_ipv4("0.0.0.0"))

    def test_foreigner_rrn(self):
        # 성별코드 5 + 체크섬 일치(외국인등록번호)
        self.assertTrue(V.validate_foreigner_rrn("900101-5123450"))
        self.assertTrue(V.rrn_is_foreigner("900101-5123450"))
        self.assertFalse(V.rrn_is_foreigner("900101-1234568"))


class TestNewDetectors(unittest.TestCase):
    def setUp(self):
        self.engine = DetectionEngine(role=ROLE_DEVELOPER)

    def _types(self, text):
        return {f.detector: f for f in self.engine.scan_text(text)}

    def test_passport(self):
        f = self._types("여권번호 M12345678 입니다.")
        self.assertIn("passport", f)
        self.assertEqual(f["passport"].severity, Severity.HIGH)
        self.assertNotIn("2345678", f["passport"].masked)

    def test_driver_license(self):
        f = self._types("운전면허 11-23-456789-01 확인.")
        self.assertIn("driver_license", f)
        self.assertEqual(f["driver_license"].confidence, Confidence.VERIFIED)

    def test_ip_developer_only(self):
        f = self._types("서버 주소 192.168.0.10 포트 8080.")
        self.assertIn("ip", f)
        self.assertEqual(f["ip"].severity, Severity.LOW)
        # 비개발 직무에는 IP 검출기 미활성
        planner = DetectionEngine(role="planner")
        self.assertNotIn("ip", planner.active_detectors)

    def test_address(self):
        f = self._types("주소: 서울특별시 강남구 테헤란로 152 입니다.")
        self.assertIn("address", f)

    def test_foreigner_type_label(self):
        findings = self.engine.scan_text("외국인등록번호 900101-5123450")
        rrn = [x for x in findings if x.detector == "rrn"]
        self.assertEqual(len(rrn), 1)
        self.assertEqual(rrn[0].info_type, "외국인등록번호")


class TestFieldRescue(unittest.TestCase):
    """컬럼 헤더 라벨로 검증 실패 후보를 구제하는 핵심 로직."""

    INVALID_RRN = "900101-1234567"  # 체크섬 불일치

    def setUp(self):
        self.engine = DetectionEngine()

    def test_dropped_without_field(self):
        # 자유 텍스트에서는 검증 실패 주민번호가 검출되지 않아야 함
        text = f"비고 {self.INVALID_RRN} 끝"
        rrns = [f for f in self.engine.scan_text(text) if f.detector == "rrn"]
        self.assertEqual(rrns, [])

    def test_rescued_in_matching_column(self):
        text = self.INVALID_RRN + "\n"
        fields = [(0, len(self.INVALID_RRN), "주민등록번호")]
        rrns = [f for f in self.engine.scan_text(text, fields) if f.detector == "rrn"]
        self.assertEqual(len(rrns), 1)
        self.assertEqual(rrns[0].severity, Severity.HIGH)          # 위험도 원복
        self.assertEqual(rrns[0].confidence, Confidence.PATTERN_ONLY)
        self.assertEqual(rrns[0].field, "주민등록번호")

    def test_not_rescued_in_unrelated_column(self):
        text = self.INVALID_RRN + "\n"
        fields = [(0, len(self.INVALID_RRN), "비고")]
        rrns = [f for f in self.engine.scan_text(text, fields) if f.detector == "rrn"]
        self.assertEqual(rrns, [])

    def test_valid_value_keeps_field_label(self):
        valid = "900101-1234568"
        text = valid + "\n"
        fields = [(0, len(valid), "주민등록번호")]
        rrns = [f for f in self.engine.scan_text(text, fields) if f.detector == "rrn"]
        self.assertEqual(len(rrns), 1)
        self.assertEqual(rrns[0].confidence, Confidence.VERIFIED)
        self.assertEqual(rrns[0].field, "주민등록번호")


class TestCsvStructuredScan(unittest.TestCase):
    def _write_csv(self, rows):
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8-sig", newline="")
        with tmp:
            csv.writer(tmp).writerows(rows)
        return Path(tmp.name)

    def test_extract_doc_fields(self):
        path = self._write_csv([["이름", "주민등록번호"], ["홍길동", "900101-1234567"]])
        try:
            doc = extract_doc(path)
            labels = {label for _, _, label in doc.fields}
            self.assertIn("주민등록번호", labels)
        finally:
            path.unlink()

    def test_invalid_rrn_rescued_via_csv_column(self):
        # 체크섬 실패 주민번호라도 '주민등록번호' 열에 있으면 검출되어야 함
        path = self._write_csv([["이름", "주민등록번호"], ["홍길동", "900101-1234567"]])
        try:
            engine = DetectionEngine()
            result = scan_file(path, engine)
            rrns = [f for f in result.findings if f.detector == "rrn"]
            self.assertEqual(len(rrns), 1)
            self.assertEqual(rrns[0].field, "주민등록번호")
            self.assertEqual(rrns[0].severity, Severity.HIGH)
        finally:
            path.unlink()


if __name__ == "__main__":
    unittest.main()
