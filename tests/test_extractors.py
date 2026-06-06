"""텍스트 추출기 단위 테스트(외부 의존성 없이 동작하는 범위)."""

import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

from soliguard.extractors import ExtractionError, extract_text, is_supported

HAS_DOCX = importlib.util.find_spec("docx") is not None


class TestPlainText(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def test_utf8(self):
        p = self.dir / "a.txt"
        p.write_text("고객 홍길동 900101-1234568", encoding="utf-8")
        self.assertIn("홍길동", extract_text(p))

    def test_cp949_autodetect(self):
        p = self.dir / "b.txt"
        p.write_bytes("계좌 110-234-567890".encode("cp949"))
        out = extract_text(p)
        self.assertIn("계좌", out)

    def test_empty(self):
        p = self.dir / "c.log"
        p.write_bytes(b"")
        self.assertEqual(extract_text(p), "")


class TestHwpx(unittest.TestCase):
    def test_hwpx_stdlib(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "doc.hwpx"
            with zipfile.ZipFile(p, "w") as z:
                z.writestr(
                    "Contents/section0.xml",
                    '<?xml version="1.0"?><hp:p>'
                    "<hp:t>고객 900101-1234568 카드 4242</hp:t></hp:p>",
                )
            out = extract_text(p)
            self.assertIn("900101-1234568", out)


class TestXlsxFallback(unittest.TestCase):
    def test_xlsx_stdlib_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "book.xlsx"
            with zipfile.ZipFile(p, "w") as z:
                z.writestr(
                    "xl/sharedStrings.xml",
                    "<sst><si><t>홍길동</t></si>"
                    "<si><t>900101-1234568</t></si></sst>",
                )
                z.writestr(
                    "xl/worksheets/sheet1.xml",
                    "<worksheet><sheetData><row>"
                    "<c><v>4242424242424242</v></c></row></sheetData></worksheet>",
                )
            out = extract_text(p)
            self.assertIn("900101-1234568", out)
            self.assertIn("4242424242424242", out)


class TestDispatch(unittest.TestCase):
    def test_unsupported(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.unknownext"
            p.write_text("hi", encoding="utf-8")
            with self.assertRaises(ExtractionError):
                extract_text(p)

    def test_is_supported(self):
        self.assertTrue(is_supported("a.txt"))
        self.assertTrue(is_supported("b.hwpx"))
        self.assertTrue(is_supported("c.PDF"))  # 대소문자 무시
        self.assertFalse(is_supported("d.exe"))

    @unittest.skipUnless(HAS_DOCX, "python-docx 미설치")
    def test_docx(self):
        import docx

        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "doc.docx"
            document = docx.Document()
            document.add_paragraph("고객 홍길동 900101-1234568")
            document.save(str(p))
            self.assertIn("900101-1234568", extract_text(p))


if __name__ == "__main__":
    unittest.main()
