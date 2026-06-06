"""설정 로드/저장 테스트."""

import json
import tempfile
import unittest
from pathlib import Path

from soliguard import config
from soliguard.config import AppConfig, ScheduleConfig


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        # 설정 경로를 임시 폴더로 격리
        config.CONFIG_DIR = Path(self.tmp.name)
        config.CONFIG_FILE = config.CONFIG_DIR / "config.json"

    def test_defaults(self):
        cfg = AppConfig.load()  # 파일 없음 → 기본값
        self.assertEqual(cfg.profile, "개발자")
        self.assertEqual(cfg.auto_action, "report_only")
        self.assertFalse(cfg.schedule.enabled)

    def test_roundtrip(self):
        cfg = AppConfig(
            profile="디자이너",
            target_folders=["C:/work"],
            ocr_mode="local",
            theme="dark",
            schedule=ScheduleConfig(enabled=True, frequency="weekly", hour=9),
            auto_action="quarantine",
        )
        cfg.save()
        loaded = AppConfig.load()
        self.assertEqual(loaded.profile, "디자이너")
        self.assertEqual(loaded.theme, "dark")
        self.assertTrue(loaded.schedule.enabled)
        self.assertEqual(loaded.schedule.frequency, "weekly")
        self.assertEqual(loaded.auto_action, "quarantine")

    def test_ignores_unknown_keys(self):
        config.CONFIG_FILE.write_text(
            json.dumps({"profile": "PM", "unknown_field": 123, "schedule": {}}),
            encoding="utf-8",
        )
        cfg = AppConfig.load()  # 알 수 없는 키 무시(상위호환)
        self.assertEqual(cfg.profile, "PM")

    def test_corrupt_file_falls_back(self):
        config.CONFIG_FILE.write_text("{ not valid json", encoding="utf-8")
        self.assertEqual(AppConfig.load().profile, "개발자")


if __name__ == "__main__":
    unittest.main()
