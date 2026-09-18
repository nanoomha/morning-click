"""오늘 순환 순서에 해당하는 그룹(3개 지점)의 순위를 조회하고, Excel에
기록한 뒤 결과를 카카오톡 "나에게 보내기"로 전송한다.

평일 09:00 자동 실행은 main_notify_schedule.py가 담당한다 (스케줄 안내 전송 직후
이 모듈의 fetch_group_ranks()/build_summary_chunks()를 그대로 불러와 이어서
순위 조회 결과까지 전송함). 이 파일은 그 로직을 담고 있으면서, 필요할 때 수동으로
다시 크롤링을 돌려보고 싶을 때 `python main_crawl.py`로 단독 실행할 수도 있다.

구글 날에는 각 지점의 google_keyword로 hearkorea.kr 홈페이지의 (광고 제외)
검색 순위를, 네이버 날에는 각 지점의 naver_keyword로 네이버 플레이스를 검색해
naver_place_name 업체의 순위를 조회한다. 같은 검색어를 쓰는 지점(예: 그룹 C의
부산 서면/사상)은 동일한 검색을 반복하지 않도록 결과를 캐싱한다.
전송은 src/kakao_sender.py가 카카오 REST API(OAuth refresh_token)를 통해 직접
처리한다(최초 1회 kakao_auth_setup.py로 인증 필요). 메시지가 너무 길어지는
경우를 대비해 결과를 여러 메시지로 나눠 순서대로 전송한다.
진단/경고 로그는 표준오류(stderr)로 보낸다.
"""
import sys
import traceback
from datetime import date
from typing import Dict, List, Optional, Tuple

from config import EXCEL_PATH, HOMEPAGE_DOMAIN, LOCATIONS, MAX_RESULTS_TO_CHECK
from src.excel_writer import append_results
from src.kakao_sender import send_text_to_me
from src.schedule_logic import GOOGLE, engine_label_ko, get_today_group_and_engine
from src.search import google_search, naver_place_search

# (지점 라벨, 검색어, 순위)
LocationResult = Tuple[str, str, Optional[int]]


def _locations_for_group(group: str) -> List[dict]:
    return [loc for loc in LOCATIONS if loc["group"] == group]


def fetch_group_ranks(group: str, engine: str) -> List[LocationResult]:
    locations = _locations_for_group(group)
    results: List[LocationResult] = []

    if engine == GOOGLE:
        rank_cache: Dict[str, Optional[int]] = {}
        for loc in locations:
            keyword = loc["google_keyword"]
            try:
                if keyword not in rank_cache:
                    rank_cache[keyword] = google_search.search_rank(
                        keyword, HOMEPAGE_DOMAIN, MAX_RESULTS_TO_CHECK
                    )
                rank = rank_cache[keyword]
            except Exception:  # noqa: BLE001 - 한 지점 실패가 전체를 막지 않도록 함
                print(f"[경고] '{keyword}'(구글) 순위 조회 실패:", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                rank = None
            results.append((loc["label"], keyword, rank))
        return results

    # 네이버: 같은 검색어를 쓰는 지점끼리는 플레이스 목록을 한 번만 조회해 재사용
    place_list_cache: Dict[str, List[str]] = {}
    for loc in locations:
        keyword = loc["naver_keyword"]
        try:
            if keyword not in place_list_cache:
                place_list_cache[keyword] = naver_place_search.fetch_place_names(
                    keyword, MAX_RESULTS_TO_CHECK
                )
            rank = naver_place_search.find_rank_by_name(
                place_list_cache[keyword], loc["naver_place_name"]
            )
        except Exception:  # noqa: BLE001
            print(f"[경고] '{keyword}'(네이버 플레이스: {loc['naver_place_name']}) 순위 조회 실패:", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            rank = None
        results.append((loc["label"], f"{keyword}→{loc['naver_place_name']}", rank))
    return results


MESSAGE_CHAR_LIMIT = 200


def build_summary_chunks(
    today: date,
    group: str,
    engine: str,
    results: List[LocationResult],
    limit: int = MESSAGE_CHAR_LIMIT,
) -> List[str]:
    """결과를 메시지 하나당 글자수 제한(기본 200자) 안에 들어가도록 여러 개로 나눈다."""
    label = engine_label_ko(engine)
    header = f"📊 나눔보청기 {group}그룹 [{label}] 순위 결과 ({today.strftime('%Y-%m-%d')})"
    lines = []
    for loc_label, _search_term, rank in results:
        rank_text = f"{rank}위" if rank is not None else "미노출"
        lines.append(f"- {loc_label}: {rank_text}")

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
    group_and_engine = get_today_group_and_engine(today)
    if group_and_engine is None:
        print("오늘은 주말/공휴일이라 순위 조회를 하지 않습니다.")
        return
    group, engine = group_and_engine

    results = fetch_group_ranks(group, engine)

    append_results(EXCEL_PATH, today, group, engine_label_ko(engine), results)

    chunks = build_summary_chunks(today, group, engine, results)
    for chunk in chunks:
        send_text_to_me(chunk)
    print("\n\n".join(chunks))


if __name__ == "__main__":
    main()
