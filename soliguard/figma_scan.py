"""Figma 클라우드 디자인 검사 모듈 (옵트인 전용).

⚠ 신뢰 설계 원칙:
  - 솔리가드의 기본 약속은 '모든 데이터 로컬 처리, 외부 미전송'.
  - Figma 검사는 본질적으로 클라우드 데이터를 가져오므로 이 약속과 충돌한다.
  - 따라서 기본 비활성. 사용자가 (1)명시적 동의 + (2)토큰 입력 한 경우에만 동작.
  - 가져온 텍스트는 메모리에서 검출에만 사용하고 디스크에 저장하지 않으며,
    검출 종료 즉시 폐기한다. 이미지·원본 디자인은 내려받지 않는다(TEXT 노드만).
  - 감사 로그에는 '검사함(파일키, 시각)'만 기록하고 내용은 남기지 않는다.

설치 의존성: requests
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .detection import DetectionEngine, Finding

log = logging.getLogger("soliguard.figma")

FIGMA_API_BASE = "https://api.figma.com/v1"

__all__ = [
    "scan_figma_file", "parse_file_key", "FigmaScanResult",
    "FigmaConsentError", "FigmaApiError",
]


class FigmaConsentError(Exception):
    """동의/토큰 없이 호출 시 - 옵트인 위반 차단."""


class FigmaApiError(Exception):
    """API 통신 실패."""


@dataclass
class FigmaScanResult:
    file_key: str
    file_name: str
    findings: list[Finding]
    text_node_count: int
    # 주의: 가져온 원본 텍스트 필드는 두지 않는다(비저장 원칙).


def scan_figma_file(
    file_key: str,
    access_token: str,
    user_consented: bool,
) -> FigmaScanResult:
    """Figma 파일의 TEXT 노드를 가져와 로컬 검출 엔진으로 검사.

    가져온 원본 텍스트는 반환하지 않고, 검출 직후 메모리에서 폐기한다.
    """
    # ── 옵트인 가드: 두 조건 모두 충족해야 진행(네트워크 호출 이전) ──
    if not user_consented:
        raise FigmaConsentError(
            "Figma 검사는 클라우드 데이터를 가져옵니다. 명시적 동의가 필요합니다."
        )
    if not access_token:
        raise FigmaConsentError("Figma 액세스 토큰이 필요합니다.")

    try:
        import requests
    except ImportError as e:
        raise FigmaApiError("Figma 검사에 requests 라이브러리가 필요합니다") from e

    headers = {"X-Figma-Token": access_token}
    try:
        resp = requests.get(
            f"{FIGMA_API_BASE}/files/{file_key}", headers=headers, timeout=30
        )
    except requests.RequestException as e:
        raise FigmaApiError(f"Figma API 연결 실패: {e}") from e

    if resp.status_code == 403:
        raise FigmaApiError("토큰이 유효하지 않거나 파일 접근 권한이 없습니다.")
    if resp.status_code == 404:
        raise FigmaApiError("파일을 찾을 수 없습니다. file_key를 확인하세요.")
    if resp.status_code != 200:
        raise FigmaApiError(f"Figma API 오류: HTTP {resp.status_code}")

    doc = resp.json()
    file_name = doc.get("name", file_key)

    # ── TEXT 노드만 수집(이미지·디자인 원본은 가져오지 않음) ──
    texts: list[str] = []
    _collect_text_nodes(doc.get("document", {}), texts)
    node_count = len(texts)

    # ── 로컬 검출 엔진으로 검사(가져온 텍스트는 메모리에만 존재) ──
    findings = DetectionEngine().scan_text("\n".join(texts))

    # ── 원본 텍스트 즉시 폐기 ──
    texts.clear()

    # ── 감사 로그: 내용 없이 메타만 기록 ──
    _audit_figma(file_key, file_name, len(findings), node_count)

    return FigmaScanResult(file_key, file_name, findings, node_count)


def _collect_text_nodes(node, acc: list[str]) -> None:
    """Figma 문서 트리를 순회하며 TEXT 노드의 characters만 수집."""
    if not isinstance(node, dict):
        return
    if node.get("type") == "TEXT":
        chars = node.get("characters")
        if isinstance(chars, str) and chars.strip():
            acc.append(chars)
    for child in node.get("children", []):
        _collect_text_nodes(child, acc)


def _audit_figma(file_key: str, file_name: str, finding_count: int, node_count: int) -> None:
    """검출 내용은 기록하지 않고 검사 사실만 남긴다."""
    from .actions import write_audit

    write_audit(
        action="figma_scan",
        path=f"figma://{file_key}",
        result="success",
        extra={
            "file_name": file_name,
            "findings": finding_count,
            "text_nodes": node_count,
        },
    )


def parse_file_key(figma_url: str) -> str:
    """Figma URL에서 파일 키 추출.

    예) https://www.figma.com/file/AbC123/제목  -> AbC123
        https://www.figma.com/design/AbC123/제목 -> AbC123
    """
    import re

    m = re.search(r"figma\.com/(?:file|design)/([A-Za-z0-9]+)", figma_url)
    if not m:
        raise ValueError("올바른 Figma 파일 URL이 아닙니다.")
    return m.group(1)
