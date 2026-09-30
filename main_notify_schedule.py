"""평일 09:00: 오늘 순환 순서(그룹/검색엔진)를 카카오톡으로 알린다.

Windows Task Scheduler는 평일마다 이 스크립트를 실행하지만, 대한민국 공휴일
(대체공휴일 포함)까지는 알지 못하므로 이 스크립트 스스로 오늘이 실제 영업일인지
확인해 아니면 조용히 종료한다. 영업일이면:

- **구글 날**: 그 그룹 3개 지점의 순위를 조회하고, `data/rank_history.xlsx`에
  저장한 뒤, 검색엔진/키워드/순위가 모두 담긴 결과를 카톡으로 전송한다
  (main_crawl.py 로직 재사용, 한 통이 200자를 넘으면 여러 통으로 자동 분할됨).
- **네이버 날**: 네이버 플레이스 순위는 현재 신뢰할 수 있는 조회 방법이 없어서
  (공식 API는 5위까지만 확인 가능, 비공식 스크래핑은 캡차 차단 위험) 실제
  순위 조회는 하지 않는다. 대신 "오늘은 어느 그룹을 네이버로 확인해야 하는
  날인지, 키워드가 뭔지"만 안내하는 메시지를 보낸다 — 수동으로 직접
  확인하실 수 있도록.

전송은 src/kakao_sender.py가 카카오 REST API(OAuth refresh_token)를 통해
직접 처리하므로 Claude 세션 등 외부 개입 없이 완전히 무인으로 동작한다.
"""
import sys
from datetime import date

# Windows 콘솔/작업 스케줄러 로그로 리다이렉트될 때 기본 인코딩(cp949)이
# 이모지(🔔, 📊 등)를 못 담아 print()가 그대로 죽는 경우가 있어, 표준입출력을
# UTF-8로 강제한다.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from config import EXCEL_PATH, LOCATIONS
from main_crawl import build_summary_chunks, fetch_group_ranks
from src.excel_writer import append_results
from src.kakao_sender import send_text_to_me
from src.schedule_logic import GOOGLE, engine_label_ko, get_today_group_and_engine


def build_naver_schedule_message(today: date, group: str) -> str:
    group_locations = [loc for loc in LOCATIONS if loc["group"] == group]
    keyword_lines = "\n".join(f"- {loc['label']}: {loc['naver_keyword']}" for loc in group_locations)
    return (
        f"🔔 나눔보청기 순위 추적 안내 ({today.strftime('%Y-%m-%d')})\n"
        f"오늘은 {group}그룹을 [네이버]로 확인하는 날입니다.\n"
        f"{keyword_lines}\n"
        f"(네이버 플레이스 자동 조회는 신뢰도 문제로 꺼져 있어, 순위는 직접 확인해주세요.)"
    )


def main() -> None:
    today = date.today()
    group_and_engine = get_today_group_and_engine(today)
    if group_and_engine is None:
        print(f"{today}: 주말/공휴일이라 오늘은 실행하지 않습니다.")
        return
    group, engine = group_and_engine

    if engine != GOOGLE:
        message = build_naver_schedule_message(today, group)
        send_text_to_me(message)
        print(message)
        return

    results = fetch_group_ranks(group, engine)
    append_results(EXCEL_PATH, today, group, engine_label_ko(engine), results)

    chunks = build_summary_chunks(today, group, engine, results)
    for chunk in chunks:
        send_text_to_me(chunk)
    print("\n\n".join(chunks))


if __name__ == "__main__":
    main()
