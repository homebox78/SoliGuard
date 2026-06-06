"""화이트리스트 - 검증된 더미/예시 패턴 제외.

2차 검증을 통과하더라도 명백한 테스트용 값(공식 테스트 카드번호,
000-0000 류의 더미 주민번호 등)은 오탐을 줄이기 위해 결과에서 제외한다.
기획서 9장 '검출 정확도' 리스크 대응.
"""

from __future__ import annotations

from .validators import digits_only

__all__ = ["is_dummy"]

# 카드사 공개 테스트 번호(Luhn은 통과하지만 실제 카드가 아님)
_TEST_CARD_NUMBERS = frozenset(
    {
        "4111111111111111",  # Visa 테스트
        "4012888888881881",  # Visa 테스트
        "4222222222222",     # Visa 13자리 테스트
        "5555555555554444",  # Mastercard 테스트
        "5105105105105100",  # Mastercard 테스트
        "378282246310005",   # Amex 테스트
        "371449635398431",   # Amex 테스트
        "6011111111111117",  # Discover 테스트
        "3530111333300000",  # JCB 테스트
        "30569309025904",    # Diners 테스트
    }
)

# 명백한 더미 주민/사업자 번호(모든 자리가 같거나 순차)
_DUMMY_SEQUENCES = frozenset(
    {
        "0" * 10, "0" * 13,
        "1234567890",
        "1234561234567",
    }
)


def is_dummy(detector: str, raw: str) -> bool:
    """검출 후보가 알려진 더미/예시 값이면 True."""
    d = digits_only(raw)

    if d in _TEST_CARD_NUMBERS or d in _DUMMY_SEQUENCES:
        return True

    # 모든 숫자가 동일(예: 1111111111111)
    if len(d) >= 6 and len(set(d)) == 1:
        return True

    return False
