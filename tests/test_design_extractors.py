"""PSD/XD 디자인 파일 추출기 테스트."""

import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from soliguard.design_extractors import (
    SUPPORTED_DESIGN, _extract_xd, _walk_xd_json, extract_design_text,
)
from soliguard.extractors import ExtractionError, extract_text, is_supported

HAS_PSD = importlib.util.find_spec("psd_tools") is not None


def _make_xd(dir_path: Path, json_obj: dict) -> Path:
    p = dir_path / "design.xd"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("artwork/artboard1.json", json.dumps(json_obj, ensure_ascii=False))
    return p


class TestXD(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def test_extract_text_node(self):
        doc = {"children": [
            {"type": "text", "text": {"rawText": "고객 홍길동 900101-1234568"}},
            {"type": "shape"},
        ]}
        self.assertIn("900101-1234568", _extract_xd(_make_xd(self.dir, doc)))

    def test_nested_text_nodes(self):
        doc = {"children": [{"children": [
            {"type": "text", "text": {"rawText": "010-1234-5678"}}]}]}
        self.assertIn("010-1234-5678", _extract_xd(_make_xd(self.dir, doc)))

    def test_invalid_zip_raises(self):
        p = self.dir / "broken.xd"
        p.write_bytes(b"not a zip file")
        with self.assertRaises(ExtractionError):
            _extract_xd(p)

    def test_ignores_non_json_entries(self):
        p = self.dir / "mixed.xd"
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("resources/image.png", b"\x89PNG\r\n")
            z.writestr("artwork/a.json", json.dumps(
                {"type": "text", "text": {"rawText": "test@example.com"}}))
        self.assertIn("test@example.com", _extract_xd(p))

    def test_dispatch_via_extract_text(self):
        # extractors.extract_text 가 디자인 분기로 연결되는지
        doc = {"type": "text", "text": {"rawText": "카드 4242424242424242"}}
        self.assertIn("4242424242424242", extract_text(_make_xd(self.dir, doc)))


class TestXDWalker(unittest.TestCase):
    def test_collects_rawtext(self):
        acc = []
        _walk_xd_json({"type": "text", "text": {"rawText": "민감정보"}}, acc)
        self.assertIn("민감정보", acc)

    def test_handles_list(self):
        acc = []
        _walk_xd_json([{"text": {"value": "리스트항목"}}], acc)
        self.assertIn("리스트항목", acc)

    def test_empty_safe(self):
        acc = []
        _walk_xd_json({}, acc)
        _walk_xd_json(None, acc)
        self.assertEqual(acc, [])


class TestDesignDispatch(unittest.TestCase):
    def test_supported_design_set(self):
        self.assertIn(".psd", SUPPORTED_DESIGN)
        self.assertIn(".xd", SUPPORTED_DESIGN)
        self.assertTrue(is_supported("a.psd"))
        self.assertTrue(is_supported("b.XD"))

    def test_unsupported_extension(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.sketch"
            p.write_bytes(b"\x00")
            with self.assertRaises(ExtractionError):
                extract_design_text(p)

    @unittest.skipUnless(HAS_PSD, "psd-tools 미설치")
    def test_psd_missing_lib_or_fixture(self):
        fixture = Path(__file__).parent / "fixtures" / "sample_with_text.psd"
        if not fixture.exists():
            self.skipTest("PSD 픽스처 없음")
        self.assertIsInstance(extract_design_text(fixture, ocr_enabled=False), str)


if __name__ == "__main__":
    unittest.main()
