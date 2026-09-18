"""영업일(평일 + 공휴일 제외) 기준으로, 오늘이 어느 그룹/어느 검색엔진을
조회하는 날인지 결정하는 로직.

12개 지점을 3개씩 A/B/C/D 그룹으로 나누고, 영업일 하루에 한 그룹씩
"구글 하루 → 네이버 하루" 순서로 8단계를 계속 순환한다:
    A구글 → A네이버 → B구글 → B네이버 → C구글 → C네이버 → D구글 → D네이버 → (다시 A구글)

주말과 대한민국 공휴일(대체공휴일 포함)은 영업일이 아니므로 건너뛰고, 순환
순서에는 영향을 주지 않는다 (건너뛴 날짜는 그냥 세지 않을 뿐).
"""
from datetime import date, timedelta
from typing import Optional, Tuple

import holidays

from config import CYCLE_REFERENCE_DATE

GOOGLE = "google"
NAVER = "naver"

# CYCLE_REFERENCE_DATE(2026-09-18)가 이 순서의 0번째(A구글)라는 실측을 기준으로 삼는다.
CYCLE_SEQUENCE = [
    ("A", GOOGLE),
    ("A", NAVER),
    ("B", GOOGLE),
    ("B", NAVER),
    ("C", GOOGLE),
    ("C", NAVER),
    ("D", GOOGLE),
    ("D", NAVER),
]

_KR_HOLIDAYS = holidays.KR()


def is_business_day(target_date: date) -> bool:
    """평일이면서 대한민국 공휴일(대체공휴일 포함)이 아닌 날인지 확인한다."""
    return target_date.weekday() < 5 and target_date not in _KR_HOLIDAYS


def _business_day_offset(target_date: date, reference_date: date) -> int:
    """reference_date를 0으로 두고, target_date까지의 영업일 수를 센다.

    reference_date와 target_date 자체가 영업일이 아니어도(주말/공휴일) 동작하며,
    두 날짜 사이의 영업일만 카운트한다. target_date가 reference_date보다 이전이면
    음수를 반환한다.
    """
    step = 1 if target_date >= reference_date else -1
    offset = 0
    current = reference_date
    while current != target_date:
        current += timedelta(days=step)
        if is_business_day(current):
            offset += step
    return offset


def get_today_group_and_engine(
    target_date: Optional[date] = None,
) -> Optional[Tuple[str, str]]:
    """오늘 조회해야 할 (그룹, 엔진)을 반환한다. 영업일이 아니면 None."""
    target_date = target_date or date.today()
    if not is_business_day(target_date):
        return None

    offset = _business_day_offset(target_date, CYCLE_REFERENCE_DATE)
    index = offset % len(CYCLE_SEQUENCE)
    return CYCLE_SEQUENCE[index]


def engine_label_ko(engine: str) -> str:
    return "구글" if engine == GOOGLE else "네이버"
