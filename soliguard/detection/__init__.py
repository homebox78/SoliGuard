"""검출 엔진 계층.

설계 원칙(기획서 6장):
- 정규식(1차 탐지)과 검증 함수(2차 검증)를 독립 모듈로 분리한다.
- 그래야 추후 문맥 기반 AI 판단으로 고도화할 때 검증 단계만 교체하면 된다.

공개 API:
    from soliguard.detection import DetectionEngine, Severity, Finding
"""

from .base import Confidence, Detector, Finding, Severity
from .engine import DetectionEngine

__all__ = [
    "DetectionEngine",
    "Detector",
    "Finding",
    "Severity",
    "Confidence",
]
