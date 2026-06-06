"""스케줄러 순수 헬퍼 테스트(외부 의존성 없이)."""

import unittest

from soliguard.config import ScheduleConfig
from soliguard.scheduler import (
    TASK_NAME, build_cron_kwargs, build_schtasks_command,
)


class TestCronKwargs(unittest.TestCase):
    def test_daily(self):
        kw = build_cron_kwargs(ScheduleConfig(frequency="daily", hour=22, minute=30))
        self.assertEqual(kw, {"hour": 22, "minute": 30})

    def test_weekly(self):
        kw = build_cron_kwargs(
            ScheduleConfig(frequency="weekly", day_of_week="mon", hour=9))
        self.assertEqual(kw["day_of_week"], "mon")
        self.assertEqual(kw["hour"], 9)

    def test_monthly(self):
        kw = build_cron_kwargs(
            ScheduleConfig(frequency="monthly", day_of_month=1, hour=8))
        self.assertEqual(kw["day"], 1)

    def test_unknown_raises(self):
        with self.assertRaises(ValueError):
            build_cron_kwargs(ScheduleConfig(frequency="hourly"))


class TestSchtasksCommand(unittest.TestCase):
    def test_weekly_command(self):
        cmd = build_schtasks_command(
            ScheduleConfig(frequency="weekly", day_of_week="mon", hour=9, minute=0),
            "C:/App/SoliGuardAgent.exe",
        )
        self.assertIn("/Create", cmd)
        self.assertIn(TASK_NAME, cmd)
        self.assertIn("WEEKLY", cmd)
        self.assertIn("MON", cmd)
        self.assertIn("09:00", cmd)
        self.assertIn("--once", " ".join(cmd))   # 1회 실행 구조

    def test_daily_command(self):
        cmd = build_schtasks_command(
            ScheduleConfig(frequency="daily", hour=7, minute=5), "agent.exe")
        self.assertIn("DAILY", cmd)
        self.assertIn("07:05", cmd)

    def test_unknown_raises(self):
        with self.assertRaises(ValueError):
            build_schtasks_command(ScheduleConfig(frequency="yearly"), "x.exe")


if __name__ == "__main__":
    unittest.main()
