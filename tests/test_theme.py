"""테마/디자인 토큰 순수 로직 테스트(Qt 불필요)."""

import unittest

from soliguard.theme import GRADE_DISPLAY, build_qss, grade_color, severity_color


class TestTheme(unittest.TestCase):
    def test_qss_light_contains_tokens(self):
        qss = build_qss("light")
        self.assertIn("#1E40AF", qss)   # SoliBlue
        self.assertIn("#F8FAFC", qss)   # light bg
        self.assertIn("QProgressBar", qss)

    def test_qss_dark_differs(self):
        light = build_qss("light")
        dark = build_qss("dark")
        self.assertNotEqual(light, dark)
        self.assertIn("#0F172A", dark)  # dark bg

    def test_unknown_theme_falls_back_to_light(self):
        self.assertEqual(build_qss("nope"), build_qss("light"))

    def test_grade_and_severity_colors(self):
        self.assertEqual(grade_color("위험"), "#DC2626")
        self.assertEqual(grade_color("안전"), "#16A34A")
        self.assertEqual(severity_color("높음"), "#DC2626")
        self.assertEqual(severity_color("낮음"), "#16A34A")
        self.assertEqual(set(GRADE_DISPLAY), {"안전", "주의", "위험"})


if __name__ == "__main__":
    unittest.main()
