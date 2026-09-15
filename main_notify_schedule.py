"""아침 9시: 오늘의 스케줄(구글/네이버 중 어떤 엔진을 검사하는 날인지) 안내를
카카오톡 "나에게 보내기"로 자동 전송한다.

Windows Task Scheduler가 매일 평일 09:00에 이 스크립트를 직접 실행하므로,
Claude 세션 등 외부 개입 없이 완전히 무인으로 동작해야 한다. 전송은
src/kakao_sender.py가 카카오 REST API(OAuth refresh_token)를 통해 직접 처리한다
(최초 1회 kakao_auth_setup.py로 인증 필요).
"""
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
