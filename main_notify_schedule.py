"""아침 9시: 오늘의 스케줄(구글/네이버 중 어떤 엔진을 검사하는 날인지) 안내 메시지를
표준출력으로 내보낸다.

카카오톡 전송은 이 스크립트가 직접 하지 않는다. Play MCP의 KakaotalkChat-MemoChat은
MCP 도구라서 Claude(에이전트) 세션 안에서만 호출할 수 있기 때문이다. 이 스크립트를
실행한 Claude 세션이 표준출력을 그대로 읽어 MemoChat(message=...)을 호출해 전송한다.
"""
from datetime import date

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
    print(build_message(date.today()))


if __name__ == "__main__":
    main()
