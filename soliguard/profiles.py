"""직무별 스캔 프로파일 메타데이터.

온보딩·스캔설정 화면이 직무에 맞는 기본값(우선 확장자·추천 폴더·OCR 기본값)을
미리 구성하는 데 쓴다. 어떤 검출기를 켜는지는 detection 패키지의 role 기반
DetectionEngine 이 담당하며, 여기서는 '스캔 범위' 기본값만 정의한다(기획서 5장 #1).
"""

from __future__ import annotations

from .engine import PROFILE_ROLE  # 직무명(한국어) → 엔진 role

__all__ = [
    "ALL_PROFILES",
    "PROFILE_EXTENSIONS",
    "PROFILE_FOLDERS",
    "PROFILE_OCR_DEFAULT",
    "PROFILE_DESC",
    "PROFILE_ICON",
    "default_scan_config",
]

#: 화면 표시 순서
ALL_PROFILES = ["개발자", "디자이너", "기획자", "PM", "전산사무"]

#: 직무별 한 줄 설명(직무 프로파일 카드용)
PROFILE_DESC = {
    "개발자": "소스코드·설정파일 속 API키·DB접속정보",
    "디자이너": "시안·PSD 이미지 속 신분증·계약서(OCR)",
    "기획자": "산출물 문서 속 실고객 샘플",
    "PM": "프로젝트 문서·일정 산출물",
    "전산사무": "명부·정산 엑셀 속 개인정보",
}

#: 직무별 아이콘(이모지)
PROFILE_ICON = {
    "개발자": "🧑‍💻", "디자이너": "🎨", "기획자": "📝",
    "PM": "📋", "전산사무": "🗂",
}

# 직무별 우선 스캔 대상 확장자
PROFILE_EXTENSIONS = {
    "개발자": {
        ".py", ".java", ".js", ".ts", ".go", ".php", ".rb", ".cs",
        ".yml", ".yaml", ".env", ".properties", ".json", ".jsonl",
        ".log", ".txt", ".csv", ".tsv", ".xlsx", ".docx", ".pdf",
        # 백업된 고객 데이터(SI 개발자 PC) — SQL 덤프·DB 파일
        ".sql", ".ddl", ".dump", ".bak", ".db", ".sqlite", ".sqlite3",
    },
    "디자이너": {
        ".psd", ".psb", ".xd",                          # 디자인 원본
        ".jpg", ".jpeg", ".png", ".bmp", ".tiff",       # 시안·리소스 이미지
        ".pdf", ".docx", ".xlsx",
    },
    "기획자": {".docx", ".hwp", ".hwpx", ".xlsx", ".csv", ".pdf", ".txt"},
    "PM": {".docx", ".hwp", ".hwpx", ".xlsx", ".csv", ".pdf", ".txt"},
    "전산사무": {".xlsx", ".csv", ".tsv", ".docx", ".hwp", ".hwpx", ".pdf",
                ".txt", ".sql", ".db", ".sqlite"},
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
