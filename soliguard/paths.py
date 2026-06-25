"""앱 데이터 저장 경로 — 단일 위치로 통일.

이전에는 설정/리포트는 platformdirs(AppData), 격리/감사로그는 ~/.soliguard 로
이원화돼 있었다. 격리·감사 이력이 이미 ~/.soliguard 에 쌓여 있고 스캔 제외
목록(DEFAULT_EXCLUDES)도 '.soliguard'를 제외하므로, 모든 앱 데이터를 이
한 곳으로 통일한다.
"""

from __future__ import annotations

from pathlib import Path

#: 모든 앱 데이터의 단일 루트
APP_DIR = Path.home() / ".soliguard"

QUARANTINE_DIR = APP_DIR / "quarantine"   # 암호화 격리함
AUDIT_DB = APP_DIR / "audit.db"           # 감사 로그(SQLite)
AUDIT_LOG_LEGACY = APP_DIR / "audit.log"  # 구형 append 로그(→ DB로 1회 마이그레이션)
CONFIG_FILE = APP_DIR / "config.json"     # 사용자 설정

__all__ = [
    "APP_DIR", "QUARANTINE_DIR", "AUDIT_DB", "AUDIT_LOG_LEGACY", "CONFIG_FILE",
    "ensure_app_dir",
]


def ensure_app_dir() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
