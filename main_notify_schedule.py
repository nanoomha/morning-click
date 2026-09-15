"""아침 9시: 오늘의 스케줄(구글/네이버 중 어떤 엔진을 검사하는 날인지) 카톡 알림."""
from datetime import date

from src.kakao_sender import send_text_to_me
from src.schedule_logic import engine_label_ko, get_today_engine


def build_message(today: date) -> str:
    engine = get_today_engine(today)
    label = engine_label_ko(engine)
    return (
        f"🔔 나눔보청기 순위 추적 안내 ({today.strftime('%Y-%m-%d')})\n"
        f"오늘은 [{label}] 검색 순위를 확인하는 날입니다.\n"
        f"10시에 자동으로 순위 조회가 진행되며, 완료 후 결과를 다시 보내드립니다."
    )


def main() -> None:
    message = build_message(date.today())
    send_text_to_me(message)
    print(message)


if __name__ == "__main__":
    main()
