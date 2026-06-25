"""업데이트 확인 — GitHub Releases 최신 버전과 현재 버전을 비교.

로컬 우선 원칙 유지: 버튼을 누를 때만 GitHub에 1회 요청하며, 개인정보는
전송하지 않는다(공개 릴리스 메타만 조회). 자동 백그라운드 확인은 하지 않는다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

REPO = "homebox78/SoliGuard"
_API = f"https://api.github.com/repos/{REPO}/releases/latest"
RELEASES_URL = f"https://github.com/{REPO}/releases"

__all__ = ["UpdateInfo", "UpdateError", "check_for_update", "RELEASES_URL"]


class UpdateError(Exception):
    """업데이트 확인 실패(네트워크/의존성/릴리스 없음 등)."""


@dataclass
class UpdateInfo:
    current: str        # 현재 버전(예: "0.4.0")
    latest: str         # 최신 릴리스 버전(예: "0.4.1")
    is_newer: bool      # 최신 > 현재
    html_url: str       # 릴리스 페이지 URL
    download_url: str   # 설치본(.exe) 다운로드 URL(없으면 릴리스 페이지)


def _ver(s: str) -> tuple:
    nums = re.findall(r"\d+", s or "")
    return tuple(int(x) for x in nums[:3]) if nums else (0,)


def _current_version() -> str:
    try:
        import soliguard
        return getattr(soliguard, "__version__", "0.0.0")
    except Exception:
        return "0.0.0"


def check_for_update(current: str | None = None, timeout: float = 8.0) -> UpdateInfo:
    """GitHub 최신 릴리스를 조회해 현재 버전과 비교. 실패 시 UpdateError."""
    try:
        import requests
    except ImportError as e:
        raise UpdateError("업데이트 확인에 requests 라이브러리가 필요합니다") from e

    cur = current or _current_version()
    try:
        r = requests.get(
            _API, timeout=timeout,
            headers={"Accept": "application/vnd.github+json"})
    except requests.RequestException as e:
        raise UpdateError(f"네트워크에 연결할 수 없습니다: {e}") from e

    if r.status_code == 404:
        raise UpdateError("아직 게시된 릴리스가 없습니다.")
    if r.status_code == 403:
        raise UpdateError("요청 한도 초과로 잠시 후 다시 시도하세요.")
    if r.status_code != 200:
        raise UpdateError(f"GitHub 응답 오류(HTTP {r.status_code})")

    data = r.json()
    tag = (data.get("tag_name") or data.get("name") or "").strip()
    if not tag:
        raise UpdateError("릴리스 버전 정보를 읽을 수 없습니다.")
    html = data.get("html_url") or RELEASES_URL
    download = ""
    for asset in data.get("assets", []):
        name = (asset.get("name") or "").lower()
        if name.endswith(".exe"):
            download = asset.get("browser_download_url", "")
            break
    return UpdateInfo(
        current=cur,
        latest=tag.lstrip("vV") or tag,
        is_newer=_ver(tag) > _ver(cur),
        html_url=html,
        download_url=download or html,
    )
