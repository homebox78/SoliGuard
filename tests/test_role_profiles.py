"""직무 프로파일 → 엔진 활성 검출기 매핑 검증.

직무 선택 시 '어떤 검출기가 추가/제외되는지'를 명세로 고정한다.
설계 원칙: 직무는 합집합-가산(union) 방식 — 공통 PII 검출기는 모든 직무에서
항상 활성이고, 직무는 전용 검출기를 '추가'만 한다(절대 제외하지 않음).
"""

import unittest

from soliguard.detection import DetectionEngine
from soliguard.detection.detectors import (
    ROLE_DESIGNER, ROLE_DEVELOPER, ROLE_FINANCE, ROLE_PM, ROLE_PLANNER,
)
from soliguard.engine import PROFILE_ROLE

# 모든 직무 공통으로 항상 활성인 검출기(범용 신원/연락/금융/주소 PII)
COMMON = {
    "rrn", "brn", "credit_card", "passport", "driver_license",
    "phone", "account", "email", "address",
}
# 개발자 직무에서만 추가되는 전용 검출기(소스/설정 산출물)
DEVELOPER_ONLY = {"secret", "ip"}


def active(role=None, roles=None):
    return set(DetectionEngine(role=role, roles=roles).active_detectors)


class TestProfileRoleMapping(unittest.TestCase):
    def test_all_profiles_mapped(self):
        self.assertEqual(
            set(PROFILE_ROLE),
            {"개발자", "디자이너", "기획자", "PM", "전산사무"},
        )

    def test_developer_adds_secret_and_ip(self):
        a = active(ROLE_DEVELOPER)
        self.assertTrue(COMMON <= a)
        self.assertEqual(a, COMMON | DEVELOPER_ONLY)

    def test_non_developer_roles_are_common_only(self):
        for role in (ROLE_DESIGNER, ROLE_PLANNER, ROLE_PM, ROLE_FINANCE):
            a = active(role)
            self.assertEqual(a, COMMON, f"{role} 활성 검출기 불일치")
            self.assertNotIn("secret", a)
            self.assertNotIn("ip", a)

    def test_common_pii_never_removed_by_role(self):
        # 어떤 직무를 골라도 범용 PII(주민/카드/전화 등)는 빠지지 않는다
        for role in PROFILE_ROLE.values():
            self.assertTrue(COMMON <= active(role), f"{role}에서 공통 PII 누락")

    def test_multi_role_is_union(self):
        # 복수 직무 = 검출기 합집합. 개발자 포함 시 전용 검출기도 합쳐진다.
        self.assertEqual(
            active(roles=[ROLE_DESIGNER, ROLE_FINANCE]), COMMON,
        )
        self.assertEqual(
            active(roles=[ROLE_DEVELOPER, ROLE_FINANCE]), COMMON | DEVELOPER_ONLY,
        )

    def test_profile_names_resolve_same_as_roles(self):
        # 한국어 직무명 → role 매핑이 동일한 활성 집합을 만든다
        self.assertEqual(
            active(PROFILE_ROLE["개발자"]), COMMON | DEVELOPER_ONLY,
        )
        self.assertEqual(active(PROFILE_ROLE["전산사무"]), COMMON)


if __name__ == "__main__":
    unittest.main()
