"""오전 10시: 오늘의 검색엔진으로 12개 키워드 순위를 조회하고,
   Excel에 기록한 뒤 결과를 카톡으로 전송한다."""
import traceback
from datetime import date
from typing import List, Optional, Tuple

from config import EXCEL_PATH, HOMEPAGE_DOMAIN, KEYWORDS, MAX_RESULTS_TO_CHECK
from src.excel_writer import append_results
from src.kakao_sender import send_text_to_me
from src.schedule_logic import GOOGLE, engine_label_ko, get_today_engine
from src.search import google_search, naver_search


def fetch_ranks(engine: str) -> List[Tuple[str, Optional[int]]]:
    search_module = google_search if engine == GOOGLE else naver_search
    results: List[Tuple[str, Optional[int]]] = []

    for keyword in KEYWORDS:
        try:
            rank = search_module.search_rank(keyword, HOMEPAGE_DOMAIN, MAX_RESULTS_TO_CHECK)
        except Exception:  # noqa: BLE001 - 한 키워드 실패가 전체를 막지 않도록 함
            print(f"[경고] '{keyword}' 순위 조회 실패:")
            traceback.print_exc()
            rank = None
        results.append((keyword, rank))

    return results


def build_summary_message(today: date, engine: str, results: List[Tuple[str, Optional[int]]]) -> str:
    label = engine_label_ko(engine)
    lines = [f"📊 나눔보청기 [{label}] 순위 결과 ({today.strftime('%Y-%m-%d')})"]
    for keyword, rank in results:
        rank_text = f"{rank}위" if rank is not None else "미노출"
        lines.append(f"- {keyword}: {rank_text}")
    return "\n".join(lines)


def main() -> None:
    today = date.today()
    engine = get_today_engine(today)

    results = fetch_ranks(engine)

    append_results(EXCEL_PATH, today, engine_label_ko(engine), results)

    message = build_summary_message(today, engine, results)
    send_text_to_me(message)
    print(message)


if __name__ == "__main__":
    main()
