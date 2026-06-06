"""PSD 테스트 픽스처 생성 스크립트.

생성물:
  sample_raster_pii.psd  : 개인정보 문자열을 '이미지로 그린' 래스터 PSD
                           → 래스터 레이어 OCR 경로 검증용(Pillow 있으면 항상 생성)

실행:  python tests/fixtures/generate_psd_fixtures.py

주의: 실제 개인 정보는 절대 사용하지 않는다(형식만 맞는 더미).
"""

from pathlib import Path

FIXTURE_DIR = Path(__file__).parent
PII_TEXT = "Phone 010-1234-5678  Card 4242-4242-4242-4242"


def make_raster_pii_psd() -> Path | None:
    """개인정보 문자열을 이미지로 렌더링한 PSD 생성(OCR 경로 검증)."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Pillow 미설치 - 래스터 PSD 픽스처 생성 건너뜀")
        return None

    img = Image.new("RGB", (900, 200), "white")
    draw = ImageDraw.Draw(img)
    font = None
    for name in ("arial.ttf", "malgun.ttf", "DejaVuSans.ttf"):
        try:
            font = ImageFont.truetype(name, 40)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()
    draw.text((20, 70), PII_TEXT, fill="black", font=font)

    out = FIXTURE_DIR / "sample_raster_pii.psd"
    try:
        from psd_tools import PSDImage

        PSDImage.frompil(img).save(out)
    except Exception:
        try:
            img.save(out, format="PSD")
        except Exception as e:
            print(f"PSD 저장 실패({e}) - 픽스처 생성 건너뜀")
            return None
    print(f"생성: {out}")
    return out


if __name__ == "__main__":
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    make_raster_pii_psd()
