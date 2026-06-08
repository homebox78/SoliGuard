"""정기 자동 스캔 에이전트 - 백그라운드 주기 실행 + Windows 작업 등록.

권장 구조: OS 작업 스케줄러(schtasks)가 '주기'를 담당하고, 에이전트 exe 는
`--once` 로 '1회 스캔'만 책임진다(재부팅·절전에도 안정적). APScheduler 상주 모드도
지원하나 보조 수단이다.

순수 헬퍼(build_cron_kwargs, build_schtasks_command)는 외부 의존성 없이 테스트된다.
"""

from __future__ import annotations

import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from .config import DATA_DIR, AppConfig, ScheduleConfig
from .engine import run_scan
from .profiles import PROFILE_OCR_DEFAULT

log = logging.getLogger("soliguard.agent")

TASK_NAME = "SoliGuard_PeriodicScan"

__all__ = [
    "build_cron_kwargs", "build_schtasks_command", "register_windows_task",
    "unregister_windows_task", "run_scheduled_scan", "run_agent",
]


# ---------------------------------------------------------------------------
# 순수 헬퍼 (테스트 대상)
# ---------------------------------------------------------------------------
def build_cron_kwargs(sched: ScheduleConfig) -> dict:
    """ScheduleConfig → APScheduler CronTrigger kwargs(순수 변환)."""
    if sched.frequency == "daily":
        return {"hour": sched.hour, "minute": sched.minute}
    if sched.frequency == "weekly":
        return {"day_of_week": sched.day_of_week, "hour": sched.hour,
                "minute": sched.minute}
    if sched.frequency == "monthly":
        return {"day": sched.day_of_month, "hour": sched.hour,
                "minute": sched.minute}
    raise ValueError(f"알 수 없는 주기: {sched.frequency}")


def build_schtasks_command(sched: ScheduleConfig, agent_exe: str | Path) -> list[str]:
    """ScheduleConfig → schtasks /Create 명령 인자 리스트(순수 생성).

    OS 작업 스케줄러가 정해진 시각에 `agent_exe --once` 를 1회 실행하도록 등록한다.
    """
    if sched.frequency == "daily":
        sc = ["/SC", "DAILY"]
    elif sched.frequency == "weekly":
        sc = ["/SC", "WEEKLY", "/D", sched.day_of_week.upper()]
    elif sched.frequency == "monthly":
        sc = ["/SC", "MONTHLY", "/D", str(sched.day_of_month)]
    else:
        raise ValueError(f"알 수 없는 주기: {sched.frequency}")

    return [
        "schtasks", "/Create", "/TN", TASK_NAME,
        "/TR", f'"{agent_exe}" --once',
        *sc,
        "/ST", f"{sched.hour:02d}:{sched.minute:02d}",
        "/F",
    ]


# ---------------------------------------------------------------------------
# Windows 작업 스케줄러 등록/해제
# ---------------------------------------------------------------------------
def _agent_exe_path() -> str:
    """배포(onefile) 시 자기 자신(SoliGuard.exe), 개발 시 'python -m soliguard.scheduler'.

    단일 exe 구조이므로 SoliGuard.exe 가 `--once` 인자를 받으면 에이전트로 동작한다
    (run_gui.py 진입점 참고). 별도 SoliGuardAgent.exe 는 더 이상 만들지 않는다.
    """
    if getattr(sys, "frozen", False):
        return sys.executable  # PyInstaller 번들된 SoliGuard.exe
    return f'{sys.executable}" -m soliguard.scheduler "'  # 개발 환경 폴백


def register_windows_task(cfg: AppConfig) -> bool:
    """Windows 작업 스케줄러에 정기 스캔 작업 등록."""
    try:
        cmd = build_schtasks_command(cfg.schedule, _agent_exe_path())
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, ValueError, OSError) as e:
        log.warning("작업 등록 실패: %s", e)
        return False


def unregister_windows_task() -> bool:
    try:
        subprocess.run(
            ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
            check=True, capture_output=True,
        )
        return True
    except (subprocess.CalledProcessError, OSError):
        return False


# ---------------------------------------------------------------------------
# 스캔 작업 본체
# ---------------------------------------------------------------------------
def run_scheduled_scan() -> None:
    """예약된 시점에 실행되는 무인 스캔 작업."""
    cfg = AppConfig.load()
    folders = [Path(f) for f in cfg.target_folders]
    if not folders:
        log.warning("스캔 대상 폴더가 설정되지 않음 - 건너뜀")
        return

    log.info("정기 스캔 시작: %s", folders)
    ocr_enabled = cfg.ocr_mode != "off" or PROFILE_OCR_DEFAULT.get(cfg.profile, False)
    summary = run_scan(
        folders, profile=cfg.profile, ocr_enabled=ocr_enabled,
        excludes=set(cfg.exclude_folders),
    )
    log.info("스캔 완료: 발견 %d건, 등급 %s",
             summary.total_findings, summary.risk_grade)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    report_path = DATA_DIR / f"report_{datetime.now():%Y%m%d_%H%M}.pdf"
    try:
        from .report import generate_pdf_report

        generate_pdf_report(summary, cfg.profile, report_path)
    except Exception as e:  # reportlab 미설치 등은 치명적이지 않음
        log.info("리포트 생성 건너뜀: %s", e)

    # 자동 격리(설정된 경우에만). 자동 완전삭제는 절대 하지 않음.
    if cfg.auto_action == "quarantine" and summary.risk_grade != "안전":
        from .actions import quarantine_file

        for r in summary.file_results:
            if any(f.severity.value == "높음" for f in r.findings):
                quarantine_file(Path(r.path))
                log.info("자동 격리: %s", r.path)

    _notify(summary, report_path)


def _notify(summary, report_path: Path) -> None:
    """사용자에게 결과 알림(윈도우 토스트, plyer 있으면)."""
    try:
        from plyer import notification

        notification.notify(
            title="SoliGuard 정기 점검 완료",
            message=f"위험 {summary.total_findings}건 발견 (등급: {summary.risk_grade})",
            timeout=10,
        )
    except Exception as e:
        log.info("알림 표시 실패(무시): %s", e)


def run_agent(argv: list[str] | None = None) -> None:
    """에이전트 진입점.

    `--once`: 1회 스캔 후 종료(OS 작업 스케줄러가 주기를 담당 — 권장).
    인자 없음: APScheduler 로 상주하며 설정 주기대로 예약(보조).
    """
    argv = sys.argv[1:] if argv is None else argv
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(DATA_DIR / "agent.log"), level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    if "--once" in argv:
        run_scheduled_scan()
        return

    cfg = AppConfig.load()
    if not cfg.schedule.enabled:
        log.info("스케줄 비활성 - 에이전트 종료")
        return

    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        log.error("APScheduler 미설치 - 상주 모드 불가(--once 권장)")
        return

    scheduler = BlockingScheduler()
    trigger = CronTrigger(**build_cron_kwargs(cfg.schedule))
    scheduler.add_job(run_scheduled_scan, trigger, id="periodic_scan",
                      misfire_grace_time=3600)
    log.info("에이전트 시작 - 주기: %s", cfg.schedule.frequency)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("에이전트 종료")


if __name__ == "__main__":
    run_agent()
