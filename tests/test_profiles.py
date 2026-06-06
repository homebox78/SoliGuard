"""직무별 스캔 프로파일 메타데이터 테스트."""

import unittest

from soliguard.profiles import (
    PROFILE_EXTENSIONS, PROFILE_FOLDERS, PROFILE_OCR_DEFAULT, default_scan_config,
)

ROLES = {"개발자", "디자이너", "기획자", "PM", "전산사무"}


class TestProfiles(unittest.TestCase):
    def test_all_profiles_present(self):
        self.assertEqual(set(PROFILE_EXTENSIONS), ROLES)
        self.assertEqual(set(PROFILE_FOLDERS), ROLES)
        self.assertEqual(set(PROFILE_OCR_DEFAULT), ROLES)

    def test_designer_includes_design_formats_and_ocr(self):
        self.assertIn(".psd", PROFILE_EXTENSIONS["디자이너"])
        self.assertIn(".xd", PROFILE_EXTENSIONS["디자이너"])
        self.assertTrue(PROFILE_OCR_DEFAULT["디자이너"])

    def test_developer_ocr_off_by_default(self):
        self.assertFalse(PROFILE_OCR_DEFAULT["개발자"])

    def test_default_scan_config(self):
        cfg = default_scan_config("디자이너")
        self.assertEqual(cfg["role"], "designer")
        self.assertTrue(cfg["ocr_enabled"])
        self.assertIn(".psd", cfg["extensions"])
        self.assertIn("시안", cfg["folders"])


if __name__ == "__main__":
    unittest.main()
