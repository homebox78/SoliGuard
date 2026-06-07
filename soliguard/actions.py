"""조치 계층: 마스킹 / 암호화 격리 / 안전 삭제(wiping) + 감사 로그.

검출 후 사용자가 선택하는 세 가지 조치를 구현한다.
- 마스킹: 검출 부분만 가린 사본 생성(원본 보존)
- 격리: AES-256-GCM 으로 암호화해 격리 폴더로 이동(복원 가능)
- 안전 삭제: 덮어쓰기 후 삭제(복구 불가), confirmed=True 일 때만 실행

모든 조치는 append-only 감사 로그에 남아 컴플라이언스 증빙이 된다.
검출 Finding 은 soliguard.detection.Finding(raw/masked 보유)을 그대로 받는다.
"""

from __future__ import annotations

import json
import os
import secrets
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence

from .extractors import _decode_bytes

# 기본 저장 위치(설정에서 변경 가능)
SOLIGUARD_HOME = Path.home() / ".soliguard"
QUARANTINE_DIR = SOLIGUARD_HOME / "quarantine"
AUDIT_LOG = SOLIGUARD_HOME / "audit.log"

__all__ = [
    "ActionResult",
    "write_audit",
    "mask_in_text_file",
    "quarantine_file",
    "restore_file",
    "secure_delete",
]


@dataclass
class ActionResult:
    action: str          # "mask" | "quarantine" | "delete" | "restore"
    path: str
    status: str          # "success" | "failed"
    detail: str = ""


# ---------------------------------------------------------------------------
# 감사 로그 (컴플라이언스 증빙)
# ---------------------------------------------------------------------------
def write_audit(
    action: str, path: str, result: str, extra: dict | None = None
) -> None:
    """모든 조치를 추가 전용(append-only) 로그로 기록."""
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "action": action,
        "path": path,
        "result": result,
        "user": os.getenv("USERNAME") or os.getenv("USER") or "unknown",
        **(extra or {}),
    }
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# 1) 마스킹: 검출 부분만 가린 사본 생성(원본 보존이 기본)
# ---------------------------------------------------------------------------
def mask_in_text_file(
    path: Path, findings: Sequence, in_place: bool = False
) -> ActionResult:
    """텍스트 파일 내 검출 문자열을 마스킹 값으로 치환.

    findings: soliguard.detection.Finding 리스트(raw, masked 보유).
    원본 인코딩(cp949 등)을 감지해 읽고, 사본은 UTF-8 로 저장한다.
    """
    path = Path(path)
    try:
        content = _decode_bytes(path.read_bytes())
        # 긴 문자열부터 치환해 부분 겹침(예: 카드번호 안의 짧은 숫자) 방지
        for f in sorted(findings, key=lambda x: -len(x.raw)):
            content = content.replace(f.raw, f.masked)

        if in_place:
            target = path
        else:
            target = path.with_name(path.stem + "_masked" + path.suffix)
        target.write_text(content, encoding="utf-8")

        write_audit(
            "mask", str(path), "success",
            {"output": str(target), "count": len(findings)},
        )
        return ActionResult("mask", str(path), "success", str(target))
    except Exception as e:
        write_audit("mask", str(path), "failed", {"error": str(e)})
        return ActionResult("mask", str(path), "failed", str(e))


# ---------------------------------------------------------------------------
# 2) 격리: AES-256-GCM 암호화 후 격리 폴더로 이동(복원 가능)
# ---------------------------------------------------------------------------
def quarantine_file(path: Path, info_type: str | None = None,
                    severity: str | None = None) -> ActionResult:
    """원본을 암호화 후 격리함으로 이동. 메타데이터로 복원 정보 보관.

    info_type/severity 가 주어지면 격리함 화면(정본 14) 표시용으로 함께 저장한다.

    주의: 데모에서는 복호화 키를 메타(.meta.json)에 함께 저장한다.
    실제 제품에서는 키를 OS 보안 저장소(Windows DPAPI 등)에 분리 저장해야
    한다 — 같은 폴더에 키를 두면 격리의 보안 의미가 사라진다.
    """
    path = Path(path)
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        msg = "격리에 cryptography 라이브러리가 필요합니다"
        write_audit("quarantine", str(path), "failed", {"error": msg})
        return ActionResult("quarantine", str(path), "failed", msg)

    try:
        QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
        key = AESGCM.generate_key(bit_length=256)
        nonce = secrets.token_bytes(12)
        aesgcm = AESGCM(key)

        data = path.read_bytes()
        encrypted = aesgcm.encrypt(nonce, data, None)

        qid = secrets.token_hex(8)
        (QUARANTINE_DIR / f"{qid}.enc").write_bytes(nonce + encrypted)
        meta = {
            "id": qid,
            "original_path": str(path),
            "quarantined_at": datetime.now().isoformat(timespec="seconds"),
            "size": len(data),
            "info_type": info_type or "",
            "severity": severity or "",
            "key": key.hex(),  # TODO(보안): OS 보안 저장소로 분리
        }
        (QUARANTINE_DIR / f"{qid}.meta.json").write_text(
            json.dumps(meta, ensure_ascii=False), encoding="utf-8"
        )

        _secure_overwrite(path)
        path.unlink()

        write_audit("quarantine", str(path), "success", {"qid": qid})
        return ActionResult("quarantine", str(path), "success", qid)
    except Exception as e:
        write_audit("quarantine", str(path), "failed", {"error": str(e)})
        return ActionResult("quarantine", str(path), "failed", str(e))


def restore_file(qid: str) -> ActionResult:
    """격리 파일을 원래 위치로 복원."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        meta_path = QUARANTINE_DIR / f"{qid}.meta.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        blob = (QUARANTINE_DIR / f"{qid}.enc").read_bytes()
        nonce, encrypted = blob[:12], blob[12:]
        aesgcm = AESGCM(bytes.fromhex(meta["key"]))
        data = aesgcm.decrypt(nonce, encrypted, None)

        target = Path(meta["original_path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

        (QUARANTINE_DIR / f"{qid}.enc").unlink()
        meta_path.unlink()
        write_audit("restore", meta["original_path"], "success", {"qid": qid})
        return ActionResult("restore", meta["original_path"], "success")
    except Exception as e:
        write_audit("restore", qid, "failed", {"error": str(e)})
        return ActionResult("restore", qid, "failed", str(e))


# ---------------------------------------------------------------------------
# 3) 안전 삭제: 덮어쓰기(wiping) 후 삭제 - 복구 불가
# ---------------------------------------------------------------------------
def _secure_overwrite(path: Path, passes: int = 3) -> None:
    """파일 내용을 난수로 여러 번 덮어써 복구를 어렵게 함.

    SSD는 wear-leveling 으로 한계가 있어, 1차 권장은 암호화 격리(기획서)."""
    length = path.stat().st_size
    if length == 0:
        return
    with open(path, "r+b", buffering=0) as f:
        for _ in range(passes):
            f.seek(0)
            f.write(secrets.token_bytes(length))
            f.flush()
            os.fsync(f.fileno())


def secure_delete(path: Path, confirmed: bool = False) -> ActionResult:
    """안전 삭제. confirmed=True(UI 확인 게이트 통과) 일 때만 실행."""
    path = Path(path)
    if not confirmed:
        # 비가역 작업은 명시적 확인 없이는 거부(화면설계서 원칙 #4)
        return ActionResult("delete", str(path), "failed", "확인 미통과")
    try:
        _secure_overwrite(path)
        path.unlink()
        write_audit("delete", str(path), "success")
        return ActionResult("delete", str(path), "success")
    except Exception as e:
        write_audit("delete", str(path), "failed", {"error": str(e)})
        return ActionResult("delete", str(path), "failed", str(e))
