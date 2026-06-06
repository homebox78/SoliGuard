"""Figma 옵트인 검사 모듈 테스트 - 가드 + 텍스트노드 수집 + (모킹) 검출."""

import importlib.util
import unittest
from unittest.mock import MagicMock, patch

from soliguard.figma_scan import (
    FigmaApiError, FigmaConsentError, _collect_text_nodes,
    parse_file_key, scan_figma_file,
)

HAS_REQUESTS = importlib.util.find_spec("requests") is not None


class TestConsentGuard(unittest.TestCase):
    """가장 중요: 동의/토큰 없으면 절대 동작 안 함."""

    def test_no_consent_blocked(self):
        with self.assertRaises(FigmaConsentError):
            scan_figma_file("KEY", "token", user_consented=False)

    def test_no_token_blocked(self):
        with self.assertRaises(FigmaConsentError):
            scan_figma_file("KEY", "", user_consented=True)

    @unittest.skipUnless(HAS_REQUESTS, "requests 미설치")
    def test_guard_runs_before_network(self):
        with patch("requests.get") as mock_get:
            with self.assertRaises(FigmaConsentError):
                scan_figma_file("KEY", "", user_consented=False)
            mock_get.assert_not_called()


class TestParseFileKey(unittest.TestCase):
    def test_file_url(self):
        self.assertEqual(
            parse_file_key("https://www.figma.com/file/AbC123/제목"), "AbC123")

    def test_design_url(self):
        self.assertEqual(
            parse_file_key("https://figma.com/design/XyZ789/x"), "XyZ789")

    def test_invalid_url(self):
        with self.assertRaises(ValueError):
            parse_file_key("https://example.com/foo")


class TestCollectTextNodes(unittest.TestCase):
    def test_collects_text_type(self):
        doc = {"type": "DOCUMENT", "children": [
            {"type": "TEXT", "characters": "주민번호 900101-1234568"},
            {"type": "RECTANGLE"},
        ]}
        acc = []
        _collect_text_nodes(doc, acc)
        self.assertEqual(acc, ["주민번호 900101-1234568"])

    def test_nested(self):
        doc = {"children": [{"type": "FRAME", "children": [
            {"type": "TEXT", "characters": "010-1234-5678"}]}]}
        acc = []
        _collect_text_nodes(doc, acc)
        self.assertIn("010-1234-5678", acc)

    def test_ignores_empty(self):
        acc = []
        _collect_text_nodes({"type": "TEXT", "characters": "   "}, acc)
        self.assertEqual(acc, [])


@unittest.skipUnless(HAS_REQUESTS, "requests 미설치")
class TestScanWithMock(unittest.TestCase):
    def _mock_response(self, status=200, doc=None, name="테스트파일"):
        resp = MagicMock()
        resp.status_code = status
        resp.json.return_value = {"name": name, "document": doc or {}}
        return resp

    def test_successful_scan_detects(self):
        doc = {"type": "DOCUMENT", "children": [
            {"type": "TEXT", "characters": "카드 4242424242424242"},
        ]}
        with patch("requests.get", return_value=self._mock_response(doc=doc)):
            with patch("soliguard.figma_scan._audit_figma"):
                result = scan_figma_file("KEY", "valid-token", user_consented=True)
        self.assertIn("신용카드번호", [f.info_type for f in result.findings])
        self.assertEqual(result.text_node_count, 1)

    def test_403_raises(self):
        with patch("requests.get", return_value=self._mock_response(status=403)):
            with self.assertRaises(FigmaApiError):
                scan_figma_file("KEY", "bad", user_consented=True)

    def test_returns_masked_only(self):
        doc = {"type": "DOCUMENT", "children": [
            {"type": "TEXT", "characters": "4242424242424242"},
        ]}
        with patch("requests.get", return_value=self._mock_response(doc=doc)):
            with patch("soliguard.figma_scan._audit_figma"):
                result = scan_figma_file("KEY", "token", user_consented=True)
        self.assertFalse(hasattr(result, "raw_text"))
        for f in result.findings:
            self.assertIn("*", f.masked)


if __name__ == "__main__":
    unittest.main()
