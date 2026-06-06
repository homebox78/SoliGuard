"""2차 검증 알고리즘 단위 테스트."""

import unittest

from soliguard.detection import validators as V


class TestRRN(unittest.TestCase):
    def test_valid_rrn(self):
        # 1990-01-01 출생, 남성(1), 체크섬 8 (수기 계산값)
        self.assertTrue(V.validate_rrn("9001011234568"))
        self.assertTrue(V.validate_rrn("900101-1234568"))  # 하이픈 허용

    def test_wrong_checksum(self):
        self.assertFalse(V.validate_rrn("9001011234567"))

    def test_invalid_date(self):
        self.assertFalse(V.validate_rrn("9013011234560"))  # 13월
        self.assertFalse(V.validate_rrn("9002301234560"))  # 2월 30일

    def test_wrong_length(self):
        self.assertFalse(V.validate_rrn("90010112345"))

    def test_foreigner_code(self):
        # 성별코드 5~8은 외국인등록번호로 분류
        self.assertFalse(V.validate_foreigner_rrn("9001011234568"))  # 코드 1


class TestLuhn(unittest.TestCase):
    def test_valid_card(self):
        self.assertTrue(V.luhn_valid("4242424242424242"))
        self.assertTrue(V.luhn_valid("4242-4242-4242-4242"))

    def test_invalid_card(self):
        self.assertFalse(V.luhn_valid("4242424242424241"))

    def test_too_short(self):
        self.assertFalse(V.luhn_valid("123456"))


class TestBRN(unittest.TestCase):
    def test_valid_brn(self):
        # 수기 계산: 123-45-6789X, 체크 = 1
        self.assertTrue(V.validate_brn("1234567891"))
        self.assertTrue(V.validate_brn("123-45-67891"))

    def test_invalid_brn(self):
        self.assertFalse(V.validate_brn("1234567890"))

    def test_wrong_length(self):
        self.assertFalse(V.validate_brn("12345"))


class TestEntropy(unittest.TestCase):
    def test_random_higher_than_repetitive(self):
        random_token = "aZ9kQ2mB7xL1pR4t"
        weak = "aaaaaaaaaaaaaaaa"
        self.assertGreater(
            V.shannon_entropy(random_token), V.shannon_entropy(weak)
        )

    def test_empty(self):
        self.assertEqual(V.shannon_entropy(""), 0.0)


if __name__ == "__main__":
    unittest.main()
