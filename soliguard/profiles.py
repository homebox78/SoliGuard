"""직무별 스캔 프로파일 메타데이터.

온보딩·스캔설정 화면이 직무에 맞는 기본값(우선 확장자·추천 폴더·OCR 기본값)을
미리 구성하는 데 쓴다. 어떤 검출기를 켜는지는 detection 패키지의 role 기반
DetectionEngine 이 담당하며, 여기서는 '스캔 범위' 기본값만 정의한다(기획서 5장 #1).
"""

from __future__ import annotations

from .engine import PROFILE_ROLE  # 직무명(한국어) → 엔진 role

__all__ = [
    "PROFILE_EXTENSIONS",
    "PROFILE_FOLDERS",
    "PROFILE_OCR_DEFAULT",
    "default_scan_config",
]

# 직무별 우선 스캔 대상 확장자
PROFILE_EXTENSIONS = {
    "개발자": {
        ".py", ".java", ".js", ".sql", ".yml", ".yaml", ".env",
        ".properties", ".json", ".log", ".txt", ".csv", ".xlsx", ".docx", ".pdf",
    },
    "디자이너": {
        ".psd", ".psb", ".xd",                          # 디자인 원본
        ".jpg", ".jpeg", ".png", ".bmp", ".tiff",       # 시안·리소스 이미지
        ".pdf", ".docx", ".xlsx",
    },
    "기획자": {".docx", ".hwp", ".hwpx", ".xlsx", ".csv", ".pdf", ".txt"},
    "PM": {".docx", ".hwp", ".hwpx", ".xlsx", ".csv", ".pdf", ".txt"},
    "전산사무": {".xlsx", ".csv", ".docx", ".hwp", ".hwpx", ".pdf", ".txt"},
}

# 직무별 권장 스캔 폴더(온보딩 기본 추천)
PROFILE_FOLDERS = {
    "개발자": ["Downloads", "Desktop", "Projects", "workspace", "git"],
    "디자이너": ["Downloads", "Desktop", "Documents", "Design", "시안", "작업"],
    "기획자": ["Downloads", "Desktop", "Documents", "산출물"],
    "PM": ["Downloads", "Desktop", "Documents", "프로젝트"],
    "전산사무": ["Downloads", "Desktop", "Documents"],
}

# 디자이너는 OCR 기본 권장(이미지로 합쳐진 개인정보 대응)
PROFILE_OCR_DEFAULT = {
    "개발자": False,
    "디자이너": True,
    "기획자": False,
    "PM": False,
    "전산사무": False,
}


def default_scan_config(profile: str) -> dict:
    """직무명으로 스캔설정 기본값 묶음을 반환(온보딩/스캔설정 UI용)."""
    return {
        "role": PROFILE_ROLE.get(profile),
        "extensions": sorted(PROFILE_EXTENSIONS.get(profile, set())),
        "folders": PROFILE_FOLDERS.get(profile, ["Downloads", "Desktop"]),
        "ocr_enabled": PROFILE_OCR_DEFAULT.get(profile, False),
    }
