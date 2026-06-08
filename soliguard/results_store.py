"""점검 결과 영속화 — 과거 스캔을 이력에서 다시 열어 상세·조치할 수 있게 한다.

개인정보 보호 원칙: 검출 '원문(raw)'은 디스크에 저장하지 않는다. 화면 표시용
마스킹 값만 보관하며, 이력에서 마스킹을 다시 적용할 때는 그 파일을 그 자리에서
재스캔해 원문을 일시 복구한다(soliguard.gui._do_action 참고). 격리·삭제는 파일
단위 작업이라 원문이 필요 없다.
"""

from __future__ import annotations

import json
import secrets
from datetime import datetime
from pathlib import Path

from .config import DATA_DIR

SCANS_DIR = DATA_DIR / "scans"

__all__ = ["save_scan", "list_scans", "load_scan", "delete_scan", "SCANS_DIR"]


def _finding_to_dict(f) -> dict:
    return {
        "detector": f.detector,
        "info_type": f.info_type,
        "severity": f.severity.value,
        "confidence": f.confidence.value,
        "masked": f.masked,          # raw 는 의도적으로 저장하지 않음(개인정보 보호)
        "start": f.start,
        "end": f.end,
        "line": f.line,
        "field": f.field,
        "weak": f.weak,
    }


def save_scan(profiles, folders, summary) -> str:
    """완료된 스캔을 JSON 으로 저장하고 스캔 id 를 반환한다.

    검출이 있거나 검사불가인 파일만 보관해 용량을 절약한다.
    """
    SCANS_DIR.mkdir(parents=True, exist_ok=True)
    sid = datetime.now().strftime("%Y%m%d_%H%M%S_") + secrets.token_hex(3)
    bysev = {"높음": 0, "중간": 0, "낮음": 0}
    results = []
    for r in summary.file_results:
        for f in r.findings:
            bysev[f.severity.value] = bysev.get(f.severity.value, 0) + 1
        if r.findings or r.status != "완료":
            results.append({
                "path": str(r.path),
                "status": r.status,
                "error": getattr(r, "error", ""),
                "findings": [_finding_to_dict(f) for f in r.findings],
            })
    data = {
        "id": sid,
        "at": datetime.now().isoformat(timespec="seconds"),
        "profiles": list(profiles),
        "folders": [str(x) for x in (folders or [])],
        "scanned": summary.scanned,
        "skipped": summary.skipped,
        "total": summary.total_findings,
        "grade": summary.risk_grade,
        "bysev": bysev,
        "results": results,
    }
    (SCANS_DIR / f"{sid}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return sid


def list_scans() -> list[dict]:
    """저장된 스캔의 요약 메타를 최신순으로 반환(상세 results 는 제외)."""
    if not SCANS_DIR.exists():
        return []
    out: list[dict] = []
    for fp in SCANS_DIR.glob("*.json"):
        try:
            d = json.loads(fp.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        out.append({k: d.get(k) for k in (
            "id", "at", "profiles", "folders", "scanned", "skipped",
            "total", "grade", "bysev")})
    out.sort(key=lambda d: d.get("at", ""), reverse=True)
    return out


def load_scan(sid: str) -> dict | None:
    """스캔 id 의 전체 데이터(상세 results 포함)를 반환. 없으면 None."""
    fp = SCANS_DIR / f"{sid}.json"
    if not fp.exists():
        return None
    try:
        return json.loads(fp.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def delete_scan(sid: str) -> None:
    try:
        (SCANS_DIR / f"{sid}.json").unlink()
    except OSError:
        pass
