"""오늘이 구글/네이버 중 어떤 엔진을 검사하는 날인지 결정하는 로직."""
from datetime import date
from typing import Optional

GOOGLE = "google"
NAVER = "naver"


def get_today_engine(target_date: Optional[date] = None) -> str:
    """날짜의 toordinal 값을 이용해 구글/네이버를 하루씩 교대로 결정한다.

    평일만 실행되므로 실행일 사이 간격은 항상 1일(월~금) 또는 3일(금->월)로
    모두 홀수이기 때문에, 실행되지 않는 주말이 껴 있어도 매 실행마다 parity가
    뒤집혀 자연스럽게 교대가 유지된다. 별도의 상태 파일 없이도 결정적으로
    동작한다.
    """
    target_date = target_date or date.today()
    return GOOGLE if target_date.toordinal() % 2 == 0 else NAVER


def engine_label_ko(engine: str) -> str:
    return "구글" if engine == GOOGLE else "네이버"
