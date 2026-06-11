"""2차 검증 알고리즘 모음.

1차 정규식이 찾아낸 후보(candidate)가 실제 유효한 값인지 가린다.
무료 도구 대비 핵심 차별점이 바로 이 검증 단계다(기획서 4장).

모든 함수는 구분자(-, 공백 등)가 섞인 원문 문자열을 그대로 받아
내부에서 숫자만 추출해 검증한다. 순수 함수이며 외부 의존성이 없다.
"""

from __future__ import annotations

import math
from collections import Counter

__all__ = [
    "digits_only",
    "is_valid_date",
    "validate_rrn",
    "validate_foreigner_rrn",
    "rrn_is_foreigner",
    "luhn_valid",
    "validate_credit_card",
    "validate_brn",
    "validate_passport",
    "validate_driver_license",
    "valid_ipv4",
    "shannon_entropy",
]


def digits_only(text: str) -> str:
    """문자열에서 숫자만 남긴다."""
    return "".join(ch for ch in text if ch.isdigit())


def is_valid_date(year: int, month: int, day: int) -> bool:
    """양력 달력상 실재하는 날짜인지 확인(윤년 포함)."""
    if not (1 <= month <= 12):
        return False
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    if leap:
        days_in_month[1] = 29
    return 1 <= day <= days_in_month[month - 1]


# 주민등록번호 체크섬 가중치(앞 12자리에 적용)
_RRN_WEIGHTS = (2, 3, 4, 5, 6, 7, 8, 9, 2, 3, 4, 5)

# 성별코드 -> 출생 세기 매핑
_RRN_CENTURY = {
    "9": 1800, "0": 1800,
    "1": 1900, "2": 1900,
    "3": 2000, "4": 2000,
    # 외국인(5~8)은 별도 함수에서 처리
    "5": 1900, "6": 1900,
    "7": 2000, "8": 2000,
}


def validate_rrn(text: str) -> bool:
    """주민등록번호(13자리) 검증.

    생년월일 유효성 + 성별코드 유효성 + 체크섬을 모두 확인한다.

    주의: 2020-10 이후 신규 발급분은 뒤 6자리가 임의 부여되어
    체크섬이 맞지 않을 수 있다. 이 경우 본 함수는 False를 반환하므로,
    엔진에서는 검증 실패 후보도 '낮음(저신뢰)' 등급으로는 남길 수 있도록
    설계한다(기획서 9장 검출 정확도 리스크 대응).
    """
    d = digits_only(text)
    if len(d) != 13:
        return False

    gender = d[6]
    if gender == "0" or gender not in _RRN_CENTURY:
        # '0'은 1800년대 코드지만 실제 사용 사례가 사실상 없어 보수적으로 제외
        if gender != "0":
            return False

    century = _RRN_CENTURY.get(gender)
    if century is None:
        return False

    year = century + int(d[0:2])
    month = int(d[2:4])
    day = int(d[4:6])
    if not is_valid_date(year, month, day):
        return False

    total = sum(int(d[i]) * _RRN_WEIGHTS[i] for i in range(12))
    check = (11 - (total % 11)) % 10
    return check == int(d[12])


def validate_foreigner_rrn(text: str) -> bool:
    """외국인등록번호 검증. 성별코드가 5~8이며 체크섬 규칙은 동일하다."""
    d = digits_only(text)
    if len(d) != 13:
        return False
    if d[6] not in ("5", "6", "7", "8"):
        return False
    return validate_rrn(text)


def rrn_is_foreigner(text: str) -> bool:
    """13자리 번호의 성별코드가 외국인(5~8)이면 True. 표시 유형 분기용."""
    d = digits_only(text)
    return len(d) == 13 and d[6] in ("5", "6", "7", "8")


def luhn_valid(text: str) -> bool:
    """신용카드 번호 Luhn 알고리즘 검증.

    13~19자리 숫자에 대해 동작한다(기획서는 13~16자리 기준).
    """
    d = digits_only(text)
    if not (13 <= len(d) <= 19):
        return False

    total = 0
    # 오른쪽에서 두 번째 자리부터 2배 처리
    reverse = d[::-1]
    for i, ch in enumerate(reverse):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def validate_credit_card(text: str) -> bool:
    """신용카드 검증 = Luhn + 브랜드 IIN(시작번호)·길이 규칙.

    Luhn만으로는 IMEI(15자리)·임의의 13/16자리 숫자가 다수 통과해 오탐이 크다.
    실제 카드 브랜드의 시작번호와 길이 조합을 함께 확인해 오탐을 줄인다."""
    d = digits_only(text)
    n = len(d)
    if n not in (13, 14, 15, 16, 19):
        return False
    if not luhn_valid(d):
        return False
    p1, p2, p3 = d[0], d[:2], d[:3]
    if n == 15:
        return p2 in ("34", "37")                       # Amex
    if n == 14:
        return p2 in ("36", "38") or p3 in (
            "300", "301", "302", "303", "304", "305", "309")  # Diners
    if n == 13:
        return p1 == "4"                                # Visa(구형 13자리)
    # 16 / 19자리: Visa(4)·Mastercard(5)·Amex계열/JCB/Diners(3)·Discover(6)
    return p1 in ("3", "4", "5", "6")


# 사업자등록번호 체크섬 가중치(앞 9자리에 적용)
_BRN_WEIGHTS = (1, 3, 7, 1, 3, 7, 1, 3, 5)


def validate_brn(text: str) -> bool:
    """사업자등록번호(10자리) 검증.

    국세청 공식 체크섬 공식:
        sum = Σ(d_i * w_i)  (i=1..9)
        sum += (d9 * 5) // 10
        check = (10 - sum % 10) % 10  == d10
    """
    d = digits_only(text)
    if len(d) != 10:
        return False

    total = sum(int(d[i]) * _BRN_WEIGHTS[i] for i in range(9))
    total += (int(d[8]) * 5) // 10
    check = (10 - (total % 10)) % 10
    return check == int(d[9])


# 한국 여권번호 발급기호(전자여권 기준): M 일반, S 긴급, R 거주여권,
# O 관용, D 외교관, G 여행증명서 등. 첫 글자가 이 집합이면 한국 여권으로 본다.
_PASSPORT_PREFIX = frozenset("MSRODGP")


def validate_passport(text: str) -> bool:
    """한국 여권번호 검증(형식 + 발급기호).

    구권: 영문 1자 + 숫자 8자(M12345678). 국제표준 신권도 동일 길이대.
    발급기호가 한국 체계에 속하고 숫자가 모두 같지 않으면 유효로 본다.
    """
    s = text.strip().upper().replace(" ", "").replace("-", "")
    if len(s) != 9:
        return False
    if s[0] not in _PASSPORT_PREFIX:
        return False
    digits = s[1:]
    if not digits.isdigit():
        return False
    return len(set(digits)) > 1


# 운전면허 지역코드(앞 2자리): 11 서울 ~ 28 권역. 신뢰 가능한 공개 범위.
_DL_REGIONS = frozenset(str(n) for n in range(11, 29))


def validate_driver_license(text: str) -> bool:
    """운전면허번호 검증. 형식(지역2-연도2-일련6-검증2) + 지역코드 유효성.

    공개된 검증번호 산식이 표준화돼 있지 않아 지역코드·자릿수·연도
    범위로 형식 검증한다(체크섬 미적용분은 컬럼 라벨로 보강 구제)."""
    d = digits_only(text)
    if len(d) != 12:
        return False
    if d[0:2] not in _DL_REGIONS:
        return False
    # 발급(취득) 연도 두 자리는 00~99 모두 허용(별도 검사 불필요).
    return len(set(d)) > 2


def valid_ipv4(text: str) -> bool:
    """IPv4 점표기 검증. 각 옥텟 0~255, 선행 0 금지, 무의미값 제외."""
    parts = text.strip().split(".")
    if len(parts) != 4:
        return False
    octets = []
    for p in parts:
        if not p.isdigit():
            return False
        if len(p) > 1 and p[0] == "0":  # 선행 0(버전 문자열 등) 배제
            return False
        v = int(p)
        if v > 255:
            return False
        octets.append(v)
    if all(o == 0 for o in octets) or all(o == 255 for o in octets):
        return False
    return True


def shannon_entropy(text: str) -> float:
    """문자열의 Shannon 엔트로피(bits/char)를 계산한다.

    API 키·시크릿처럼 무작위성이 높은 문자열을 일반 식별자와
    구분하는 데 사용한다. 영문/숫자가 고루 섞인 토큰은 보통 3.5 이상.
    """
    if not text:
        return 0.0
    counts = Counter(text)
    n = len(text)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())
