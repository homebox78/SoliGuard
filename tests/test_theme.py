"""테마/디자인 토큰 순수 로직 테스트(Qt 불필요)."""

import unittest

from soliguard.theme import (
    GRADE_DISPLAY, SEV_CHIP, build_qss, grade_color, severity_color,
)


class TestTheme(unittest.TestCase):
    def test_qss_light_contains_tokens(self):
        qss = build_qss("light")
        self.assertIn("#B0123F", qss)     # solideo 크림슨(정본 brand)
        self.assertIn("#F7F8FA", qss)     # 쿨그레이 보조 배경(surfaceAlt)
        self.assertIn("Pretendard", qss)  # 폰트 통일
        self.assertIn("#Sidebar", qss)

    def test_unknown_theme_falls_back_to_light(self):
        self.assertEqual(build_qss("nope"), build_qss("light"))

    def test_grade_and_severity_colors(self):
        self.assertEqual(grade_color("위험"), "#B0123F")
        self.assertEqual(grade_color("안전"), "#15A34A")
        self.assertEqual(severity_color("높음"), "#B0123F")
        self.assertEqual(severity_color("낮음"), "#15A34A")
        self.assertEqual(set(GRADE_DISPLAY), {"안전", "주의", "위험"})
        self.assertEqual(set(SEV_CHIP), {"높음", "중간", "낮음"})


if __name__ == "__main__":
    unittest.main()
