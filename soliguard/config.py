"""사용자 설정 로드/저장 - OS 표준 경로에 JSON 보관.

platformdirs 가 있으면 OS 표준 경로를, 없으면 ~/.soliguard 로 폴백한다.
설정은 온보딩·스케줄러·설정 화면이 공유한다.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

try:
    from platformdirs import user_config_dir, user_data_dir

    CONFIG_DIR = Path(user_config_dir("SoliGuard", "Solideo"))
    DATA_DIR = Path(user_data_dir("SoliGuard", "Solideo"))
except ImportError:  # 폴백: actions 와 동일한 홈 디렉터리 계열
    _HOME = Path.home() / ".soliguard"
    CONFIG_DIR = _HOME
    DATA_DIR = _HOME / "data"

CONFIG_FILE = CONFIG_DIR / "config.json"

__all__ = ["AppConfig", "ScheduleConfig", "CONFIG_DIR", "DATA_DIR", "CONFIG_FILE"]


@dataclass
class ScheduleConfig:
    enabled: bool = False
    frequency: str = "weekly"      # "daily" | "weekly" | "monthly"
    day_of_week: str = "mon"       # weekly용 (mon~sun)
    day_of_month: int = 1          # monthly용
    hour: int = 9
    minute: int = 0


@dataclass
class AppConfig:
    profile: str = "개발자"                # 대표 직무(하위호환)
    profiles: list[str] = field(default_factory=list)  # 복수 선택 직무
    target_folders: list[str] = field(default_factory=list)
    ocr_mode: str = "local"            # "local" | "off" | "cloud"(동의 시)
    exclude_folders: list[str] = field(default_factory=list)
    theme: str = "light"               # "light" | "dark"
    schedule: ScheduleConfig = field(default_factory=ScheduleConfig)
    # 자동 스캔 시 발견만 할지(report_only), 위험 파일 자동 격리까지 할지.
    # 자동 완전삭제는 의도적으로 제공하지 않는다(사고 방지).
    auto_action: str = "report_only"   # "report_only" | "quarantine"
    last_grade: str = "safe"           # 트레이 아이콘 색용 캐시
    whitelist: list[str] = field(default_factory=list)  # 사용자 지정 오탐(제외) 값

    @classmethod
    def load(cls) -> "AppConfig":
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return cls()
            sched = ScheduleConfig(**data.pop("schedule", {}))
            # 알 수 없는 키는 무시(상위 호환)
            known = {f.name for f in cls.__dataclass_fields__.values()}
            data = {k: v for k, v in data.items() if k in known}
            return cls(schedule=sched, **data)
        return cls()

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(
            json.dumps(asdict(self), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
