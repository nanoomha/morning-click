"""아침 9시: 오늘의 스케줄 안내와 검색 순위 조회 결과를 한 번에 카카오톡으로
전송한다.

Windows Task Scheduler가 매일 평일 09:00에 이 스크립트 하나만 실행하면
스케줄 안내 → 순위 크롤링 → 결과 전송까지 이어서 처리되도록, 기존에 10시에
따로 실행하던 순위 조회(main_crawl.py)를 이 스크립트 안에서 그대로 호출한다.
전송은 src/kakao_sender.py가 카카오 REST API(OAuth refresh_token)를 통해
직접 처리하므로 Claude 세션 등 외부 개입 없이 완전히 무인으로 동작한다.
"""
from datetime import date

from config import EXCEL_PATH
from main_crawl import build_summary_chunks, fetch_ranks
from src.excel_writer import append_results
from src.kakao_sender import send_text_to_me
from src.schedule_logic import engine_label_ko, get_today_engine


def build_schedule_message(today: date, engine: str) -> str:
    label = engine_label_ko(engine)
    return (
        f"🔔 나눔보청기 순위 추적 안내 ({today.strftime('%Y-%m-%d')})\n"
        f"오늘은 [{label}] 검색 순위를 확인하는 날입니다.\n"
        f"잠시 후 순위 조회 결과를 이어서 보내드립니다."
    )


def main() -> None:
    today = date.today()
    engine = get_today_engine(today)

    schedule_message = build_schedule_message(today, engine)
    send_text_to_me(schedule_message)
    print(schedule_message)

    results = fetch_ranks(engine)
    append_results(EXCEL_PATH, today, engine_label_ko(engine), results)

    chunks = build_summary_chunks(today, engine, results)
    for chunk in chunks:
        send_text_to_me(chunk)
    print("\n\n".join(chunks))


if __name__ == "__main__":
    main()
