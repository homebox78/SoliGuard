"""디자인 파일(PSD/XD) 텍스트 추출 - 텍스트 레이어 우선, 래스터는 OCR 폴백.

디자이너 직무 차별점: 시안·목업에 잘못 삽입된 실고객 정보(텍스트 또는 이미지)를
잡아낸다. 통일 인터페이스 `extract_text(path) -> str`(extractors)에 연결된다.

- PSD: psd-tools 로 텍스트 레이어 직접 추출(OCR 불필요), 래스터/스마트오브젝트는 OCR
- XD: ZIP 컨테이너 내부 JSON 텍스트 노드 추출(표준 라이브러리만으로 동작)
- Figma: 클라우드 저장이 기본이라 'figma_scan' 옵트인 모듈로 분리

설치 의존성(선택): psd-tools(PSD), Pillow+pytesseract(래스터 OCR)
"""

from __future__ import annotations

import json
import logging
import zipfile
from pathlib import Path

from .extractors import SUPPORTED_DESIGN, ExtractionError

__all__ = ["extract_design_text", "SUPPORTED_DESIGN"]

log = logging.getLogger("soliguard.design")

# OCR 성능 보호 상한
_OCR_MAX_PIXELS = 4000 * 4000
_OCR_MAX_RASTER_LAYERS = 30
# XD 내부 텍스트가 담기는 대표 키(버전마다 달라 폭넓게 탐색)
_XD_TEXT_KEYS = ("rawText", "text", "value", "content")


def extract_design_text(path: Path, ocr_enabled: bool = True) -> str:
    """디자인 파일에서 텍스트 추출. 확장자별 분기."""
    path = Path(path)
    ext = path.suffix.lower()
    if ext in (".psd", ".psb"):
        return _extract_psd(path, ocr_enabled)
    if ext == ".xd":
        return _extract_xd(path)
    raise ExtractionError(f"지원하지 않는 디자인 형식: {ext}")


# ---------------------------------------------------------------------------
# PSD (Photoshop)
# ---------------------------------------------------------------------------
def _extract_psd(path: Path, ocr_enabled: bool) -> str:
    """PSD 텍스트 레이어 추출 + (옵션) 래스터 레이어 OCR."""
    try:
        from psd_tools import PSDImage
    except ImportError as e:
        raise ExtractionError("psd-tools 미설치로 PSD 검사 불가") from e

    try:
        psd = PSDImage.open(path)
    except Exception as e:
        raise ExtractionError(f"PSD 열기 실패: {e}") from e

    text_parts: list[str] = []
    raster_layers = []
    for layer in psd.descendants():
        kind = getattr(layer, "kind", None)
        if kind == "type":  # 텍스트 레이어 - 가장 정확한 경로(OCR 불필요)
            try:
                if layer.text:
                    text_parts.append(layer.text)
            except Exception as ex:
                log.debug("텍스트 레이어 추출 실패(무시): %s", ex)
        elif ocr_enabled and kind in ("pixel", "smartobject"):
            is_visible = getattr(layer, "is_visible", None)
            if is_visible is None or is_visible():
                raster_layers.append(layer)

    if ocr_enabled and raster_layers:
        text_parts.extend(_ocr_psd_layers(raster_layers))

    return "\n".join(p for p in text_parts if p and p.strip())


def _ocr_psd_layers(layers) -> list[str]:
    """PSD 래스터 레이어들을 이미지로 합성해 OCR(상한 적용)."""
    try:
        import pytesseract
    except ImportError:
        log.info("pytesseract 미설치 - PSD 래스터 OCR 건너뜀")
        return []

    out: list[str] = []
    for layer in layers[:_OCR_MAX_RASTER_LAYERS]:
        try:
            img = layer.composite()
            if img is None:
                continue
            if img.width * img.height > _OCR_MAX_PIXELS:
                img.thumbnail((4000, 4000))
            txt = pytesseract.image_to_string(img, lang="kor+eng")
            if txt.strip():
                out.append(txt)
        except Exception as ex:
            log.debug("PSD 레이어 OCR 실패(무시): %s", ex)
    return out


# ---------------------------------------------------------------------------
# XD (Adobe XD) - ZIP 컨테이너 내부 JSON
# ---------------------------------------------------------------------------
def _extract_xd(path: Path) -> str:
    """XD(.xd)는 ZIP. 내부 *.json 에서 텍스트 노드 추출(표준 라이브러리)."""
    if not zipfile.is_zipfile(path):
        raise ExtractionError("유효한 XD(ZIP) 파일이 아님")

    texts: list[str] = []
    with zipfile.ZipFile(path) as zf:
        for name in zf.namelist():
            if not name.endswith(".json"):
                continue
            try:
                data = json.loads(zf.read(name).decode("utf-8", "replace"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            _walk_xd_json(data, texts)
    return "\n".join(t for t in texts if t and t.strip())


def _walk_xd_json(node, acc: list[str]) -> None:
    """JSON 트리를 재귀 순회하며 텍스트 노드 문자열 수집(버전별 키 폭넓게 탐색).

    각 노드에서 텍스트 키(문자열 값)는 한 번만 수집하고, 중첩 dict/list 는
    재귀로 내려간다. 이렇게 하면 같은 텍스트가 중복 수집되지 않는다.
    """
    if isinstance(node, dict):
        for k in _XD_TEXT_KEYS:
            v = node.get(k)
            if isinstance(v, str) and v.strip():
                acc.append(v)
        for v in node.values():
            if isinstance(v, (dict, list)):
                _walk_xd_json(v, acc)
    elif isinstance(node, list):
        for item in node:
            _walk_xd_json(item, acc)
