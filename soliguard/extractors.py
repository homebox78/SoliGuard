"""파일 포맷별 텍스트 추출 - 검출 엔진에 통일된 텍스트를 공급.

통일 인터페이스 `extract_text(path) -> str` 로 모든 포맷을 텍스트로 받는다.
포맷별 라이브러리를 지연 import 하여, 라이브러리가 없거나 파싱이 실패해도
ExtractionError 로 격리되어 전체 스캔이 멈추지 않는다(기획서 9장 리스크 #3).

기본 동작(외부 의존성 없이):
    - 평문/소스/로그: 표준 라이브러리(인코딩 자동 감지)
    - hwpx: zip+xml 파싱(표준 라이브러리)  ← 국내 SI 차별점
    - xlsx: openpyxl 있으면 사용, 없으면 zip+xml 폴백

선택 라이브러리(있으면 활성):
    openpyxl, xlrd, python-docx, pdfplumber, olefile, pytesseract, Pillow, chardet
"""

from __future__ import annotations

import re
import struct
import zipfile
import zlib
from pathlib import Path

__all__ = ["extract_text", "ExtractionError", "is_supported"]


class ExtractionError(Exception):
    """파싱 불가(암호/손상/미지원/라이브러리 없음) 시 발생 → '검사불가' 처리."""


SUPPORTED_TEXT = {
    ".txt", ".csv", ".log", ".json", ".xml", ".md", ".py", ".java", ".js",
    ".ts", ".kt", ".go", ".sql", ".yml", ".yaml", ".ini", ".cfg",
    ".properties", ".env", ".html", ".sh", ".bat", ".ps1",
}
SUPPORTED_OFFICE = {".xlsx", ".xls", ".docx"}
SUPPORTED_HWP = {".hwp", ".hwpx"}
SUPPORTED_PDF = {".pdf"}
SUPPORTED_IMAGE = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
# 디자인 파일(디자이너 직무). 실제 추출은 design_extractors 가 담당.
SUPPORTED_DESIGN = {".psd", ".psb", ".xd"}

_ALL_SUPPORTED = (
    SUPPORTED_TEXT | SUPPORTED_OFFICE | SUPPORTED_HWP | SUPPORTED_PDF
    | SUPPORTED_IMAGE | SUPPORTED_DESIGN
)


def is_supported(path: str | Path) -> bool:
    return Path(path).suffix.lower() in _ALL_SUPPORTED


def extract_text(path: str | Path, ocr_enabled: bool = True) -> str:
    """확장자에 맞는 추출기로 분기. 실패 시 ExtractionError."""
    path = Path(path)
    ext = path.suffix.lower()
    try:
        if ext in SUPPORTED_TEXT:
            return _extract_plain(path)
        if ext == ".xlsx":
            return _extract_xlsx(path)
        if ext == ".xls":
            return _extract_xls(path)
        if ext == ".docx":
            return _extract_docx(path)
        if ext == ".hwpx":
            return _extract_hwpx(path)
        if ext == ".hwp":
            return _extract_hwp_ole(path)
        if ext == ".pdf":
            return _extract_pdf(path, ocr_enabled)
        if ext in SUPPORTED_IMAGE:
            return _extract_image(path) if ocr_enabled else ""
        if ext in SUPPORTED_DESIGN:
            from .design_extractors import extract_design_text

            return extract_design_text(path, ocr_enabled)
        raise ExtractionError(f"미지원 형식: {ext}")
    except ExtractionError:
        raise
    except Exception as e:  # 포맷 라이브러리의 모든 예외를 격리
        raise ExtractionError(f"{path.name} 파싱 실패: {e}") from e


# ---------------------------------------------------------------------------
# 평문 / 소스 / 로그
# ---------------------------------------------------------------------------
def _extract_plain(path: Path) -> str:
    """텍스트/소스/로그 - 인코딩 자동 감지(한글 cp949 대응)."""
    raw = path.read_bytes()
    if not raw:
        return ""
    return _decode_bytes(raw)


def _decode_bytes(raw: bytes) -> str:
    # chardet 있으면 1차로 활용
    try:
        import chardet  # type: ignore

        guessed = chardet.detect(raw[:100_000]).get("encoding")
        if guessed:
            try:
                return raw.decode(guessed, errors="replace")
            except LookupError:
                pass
    except ImportError:
        pass
    # 폴백: 흔한 인코딩 순차 시도(국내 SI는 cp949/euc-kr 빈번)
    for enc in ("utf-8-sig", "utf-8", "cp949", "euc-kr"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


# ---------------------------------------------------------------------------
# 엑셀
# ---------------------------------------------------------------------------
def _extract_xlsx(path: Path) -> str:
    """엑셀(xlsx). openpyxl 있으면 사용, 없으면 zip+xml 폴백."""
    try:
        import openpyxl  # type: ignore
    except ImportError:
        return _extract_xlsx_stdlib(path)

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    parts: list[str] = []
    try:
        for ws in wb.worksheets:
            for row in ws.iter_rows(values_only=True):
                cells = [str(c) for c in row if c is not None]
                if cells:
                    parts.append(" ".join(cells))
    finally:
        wb.close()
    return "\n".join(parts)


def _extract_xlsx_stdlib(path: Path) -> str:
    """openpyxl 없이 xlsx에서 텍스트 추출(검출 목적의 폴백).

    sharedStrings 의 <t> 텍스트와 각 시트의 <v> 값을 모아 검출 엔진에 넘긴다.
    숫자로 저장된 PII(예: 숫자형 셀의 카드번호)도 <v> 로 포착된다.
    """
    if not zipfile.is_zipfile(path):
        raise ExtractionError("유효한 xlsx(zip) 가 아님")
    parts: list[str] = []
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if "xl/sharedStrings.xml" in names:
            xml = z.read("xl/sharedStrings.xml").decode("utf-8", errors="replace")
            parts += re.findall(r"<t[^>]*>(.*?)</t>", xml, re.DOTALL)
        for name in names:
            if name.startswith("xl/worksheets/") and name.endswith(".xml"):
                xml = z.read(name).decode("utf-8", errors="replace")
                parts += re.findall(r"<v>(.*?)</v>", xml, re.DOTALL)
    return "\n".join(_strip_xml(p) for p in parts)


def _extract_xls(path: Path) -> str:
    """구형 엑셀(xls) - xlrd 필요."""
    try:
        import xlrd  # type: ignore
    except ImportError:
        raise ExtractionError("xls 파싱에 xlrd 라이브러리가 필요합니다")
    book = xlrd.open_workbook(path)
    parts: list[str] = []
    for sheet in book.sheets():
        for r in range(sheet.nrows):
            cells = [str(c) for c in sheet.row_values(r) if c != ""]
            if cells:
                parts.append(" ".join(cells))
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 워드
# ---------------------------------------------------------------------------
def _extract_docx(path: Path) -> str:
    """워드(docx) - 본문 단락 + 표 셀. python-docx 필요."""
    try:
        import docx  # type: ignore
    except ImportError:
        raise ExtractionError("docx 파싱에 python-docx 라이브러리가 필요합니다")
    doc = docx.Document(str(path))
    parts = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text for cell in row.cells if cell.text.strip()]
            if cells:
                parts.append(" ".join(cells))
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 한글(hwp/hwpx) - 국내 SI 환경 필수
# ---------------------------------------------------------------------------
def _extract_hwpx(path: Path) -> str:
    """hwpx: zip 내부 Contents/section*.xml 의 <hp:t> 텍스트 추출(표준 라이브러리)."""
    if not zipfile.is_zipfile(path):
        raise ExtractionError("유효한 hwpx(zip) 가 아님")
    parts: list[str] = []
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if "section" in name.lower() and name.endswith(".xml"):
                xml = z.read(name).decode("utf-8", errors="replace")
                parts += re.findall(r"<hp:t>(.*?)</hp:t>", xml, re.DOTALL)
    return "\n".join(_strip_xml(p) for p in parts)


def _extract_hwp_ole(path: Path) -> str:
    """구형 hwp: OLE BodyText 스트림(zlib 압축) 해제 후 텍스트 추출. olefile 필요."""
    try:
        import olefile  # type: ignore
    except ImportError:
        raise ExtractionError("hwp 파싱에 olefile 라이브러리가 필요합니다")

    if not olefile.isOleFile(str(path)):
        raise ExtractionError("유효한 HWP(OLE) 파일이 아님")
    ole = olefile.OleFileIO(str(path))
    try:
        header = ole.openstream("FileHeader").read()
        is_compressed = bool(header[36] & 0x01)
        is_encrypted = bool(header[36] & 0x02)
        if is_encrypted:
            raise ExtractionError("암호로 보호된 HWP 문서")

        texts: list[str] = []
        for entry in ole.listdir():
            if entry[0] == "BodyText":
                data = ole.openstream(entry).read()
                if is_compressed:
                    data = zlib.decompress(data, -15)
                texts.append(_decode_hwp_records(data))
        return "\n".join(texts)
    finally:
        ole.close()


def _decode_hwp_records(data: bytes) -> str:
    """HWP 레코드 구조에서 PARA_TEXT(태그 67, UTF-16LE) 추출."""
    out: list[str] = []
    i, n = 0, len(data)
    while i + 4 <= n:
        header = struct.unpack("<I", data[i : i + 4])[0]
        tag = header & 0x3FF
        size = (header >> 20) & 0xFFF
        i += 4
        if tag == 67:  # HWPTAG_PARA_TEXT
            chunk = data[i : i + size]
            out.append(chunk.decode("utf-16-le", errors="replace"))
        i += size
    return "".join(out)


# ---------------------------------------------------------------------------
# PDF / 이미지(OCR)
# ---------------------------------------------------------------------------
def _extract_pdf(path: Path, ocr_enabled: bool) -> str:
    """PDF - 텍스트 레이어 우선, 없으면(스캔 PDF) OCR 폴백. pdfplumber 필요."""
    try:
        import pdfplumber  # type: ignore
    except ImportError:
        raise ExtractionError("pdf 파싱에 pdfplumber 라이브러리가 필요합니다")

    parts: list[str] = []
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            parts.append(page.extract_text() or "")
    text = "\n".join(parts).strip()
    if not text and ocr_enabled:
        return _ocr_pdf(path)
    return text


def _extract_image(path: Path) -> str:
    """이미지 OCR - 신분증·계약서 스캔본(로컬 Tesseract 기본). pytesseract 필요."""
    try:
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore
    except ImportError:
        raise ExtractionError("이미지 OCR에 pytesseract/Pillow 가 필요합니다")
    img = Image.open(str(path))
    return pytesseract.image_to_string(img, lang="kor+eng")


def _ocr_pdf(path: Path) -> str:
    """스캔 PDF를 이미지로 변환 후 OCR. pdf2image + pytesseract 필요."""
    try:
        from pdf2image import convert_from_path  # type: ignore
        import pytesseract  # type: ignore
    except ImportError:
        raise ExtractionError("스캔 PDF OCR에 pdf2image/pytesseract 가 필요합니다")
    parts = [
        pytesseract.image_to_string(img, lang="kor+eng")
        for img in convert_from_path(str(path), dpi=200)
    ]
    return "\n".join(parts)


# ---------------------------------------------------------------------------
def _strip_xml(text: str) -> str:
    """잔여 XML 태그 제거 + 기본 엔티티 복원."""
    text = re.sub(r"<[^>]+>", "", text)
    return (
        text.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#xD;", "")
    )
