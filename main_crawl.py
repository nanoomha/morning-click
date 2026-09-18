"""오늘의 검색엔진으로 12개 키워드 순위를 조회하고, Excel에 기록한 뒤 결과를
카카오톡 "나에게 보내기"로 전송한다.

평일 09:00 자동 실행은 main_notify_schedule.py가 담당한다 (스케줄 안내 전송 직후
이 모듈의 fetch_ranks()/build_summary_chunks()를 그대로 불러와 이어서 순위 조회
결과까지 전송함). 이 파일은 그 로직을 담고 있으면서, 필요할 때 수동으로 다시
크롤링을 돌려보고 싶을 때 `python main_crawl.py`로 단독 실행할 수도 있다.
전송은 src/kakao_sender.py가 카카오 REST API(OAuth refresh_token)를 통해 직접
처리한다(최초 1회 kakao_auth_setup.py로 인증 필요). 메시지가 너무 길어지는
경우를 대비해 결과를 여러 메시지로 나눠 순서대로 전송한다.
진단/경고 로그는 표준오류(stderr)로 보낸다.
"""
import sys
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
            print(f"[경고] '{keyword}' 순위 조회 실패:", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            rank = None
        results.append((keyword, rank))

    return results


MESSAGE_CHAR_LIMIT = 200


def build_summary_chunks(
    today: date,
    engine: str,
    results: List[Tuple[str, Optional[int]]],
    limit: int = MESSAGE_CHAR_LIMIT,
) -> List[str]:
    """결과를 메시지 하나당 글자수 제한(기본 200자) 안에 들어가도록 여러 개로 나눈다.

    키워드가 늘거나 순위 자릿수가 커져도 한 메시지가 제한을 넘지 않도록 항상
    안전하게 분할한다.
    """
    label = engine_label_ko(engine)
    header = f"📊 나눔보청기 [{label}] 순위 결과 ({today.strftime('%Y-%m-%d')})"
    lines = []
    for keyword, rank in results:
        rank_text = f"{rank}위" if rank is not None else "미노출"
        lines.append(f"- {keyword}: {rank_text}")

    chunks: List[str] = []
    current = [header]
    for line in lines:
        candidate = current + [line]
        if len("\n".join(candidate)) > limit:
            chunks.append("\n".join(current))
            current = ["(계속)", line]
        else:
            current = candidate
    chunks.append("\n".join(current))
    return chunks


def main() -> None:
    today = date.today()
    engine = get_today_engine(today)

    results = fetch_ranks(engine)

    append_results(EXCEL_PATH, today, engine_label_ko(engine), results)

    chunks = build_summary_chunks(today, engine, results)
    for chunk in chunks:
        send_text_to_me(chunk)
    print("\n\n".join(chunks))


if __name__ == "__main__":
    main()
