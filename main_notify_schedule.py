"""아침 9시: 오늘의 스케줄 안내와 검색 순위 조회 결과를 한 번에 카카오톡으로
전송한다.

Windows Task Scheduler는 평일마다 이 스크립트를 실행하지만, 대한민국 공휴일
(대체공휴일 포함)까지는 알지 못하므로 이 스크립트 스스로 오늘이 실제 영업일인지
확인해 아니면 조용히 종료한다. 영업일이면 다음을 순서대로 처리한다.
  1. 오늘이 어느 그룹(A/B/C/D)·어느 검색엔진(구글/네이버) 차례인지 안내 전송
  2. 이어서 곧바로 그 그룹 3개 지점의 순위를 조회 (main_crawl.py 로직 재사용)
  3. `data/rank_history.xlsx`에 결과 누적 저장
  4. 순위 결과를 카카오톡으로 전송

전송은 src/kakao_sender.py가 카카오 REST API(OAuth refresh_token)를 통해
직접 처리하므로 Claude 세션 등 외부 개입 없이 완전히 무인으로 동작한다.
"""
from datetime import date

from config import EXCEL_PATH
from main_crawl import build_summary_chunks, fetch_group_ranks
from src.excel_writer import append_results
from src.kakao_sender import send_text_to_me
from src.schedule_logic import engine_label_ko, get_today_group_and_engine


def build_schedule_message(today: date, group: str, engine: str) -> str:
    label = engine_label_ko(engine)
    return (
        f"🔔 나눔보청기 순위 추적 안내 ({today.strftime('%Y-%m-%d')})\n"
        f"오늘은 {group}그룹을 [{label}]로 확인하는 날입니다.\n"
        f"잠시 후 순위 조회 결과를 이어서 보내드립니다."
    )


def main() -> None:
    today = date.today()
    group_and_engine = get_today_group_and_engine(today)
    if group_and_engine is None:
        print(f"{today}: 주말/공휴일이라 오늘은 실행하지 않습니다.")
        return
    group, engine = group_and_engine

    schedule_message = build_schedule_message(today, group, engine)
    send_text_to_me(schedule_message)
    print(schedule_message)

    results = fetch_group_ranks(group, engine)
    append_results(EXCEL_PATH, today, group, engine_label_ko(engine), results)

    chunks = build_summary_chunks(today, group, engine, results)
    for chunk in chunks:
        send_text_to_me(chunk)
    print("\n\n".join(chunks))


if __name__ == "__main__":
    main()
