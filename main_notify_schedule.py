"""평일 09:00: 오늘 순환 순서(그룹/검색엔진)에 맞춰 순위를 조회하고,
날짜/검색엔진/키워드/순위가 모두 담긴 결과를 카카오톡으로 한 번에 전송한다.

Windows Task Scheduler는 평일마다 이 스크립트를 실행하지만, 대한민국 공휴일
(대체공휴일 포함)까지는 알지 못하므로 이 스크립트 스스로 오늘이 실제 영업일인지
확인해 아니면 조용히 종료한다. 영업일이면:
  1. 오늘 그룹(A/B/C/D)·검색엔진(구글/네이버)에 맞춰 그 그룹 3개 지점의 순위 조회
     (main_crawl.py 로직 재사용)
  2. `data/rank_history.xlsx`에 결과 누적 저장
  3. 검색엔진/키워드/순위가 모두 담긴 결과 메시지를 카카오톡으로 전송 (한 통이
     200자를 넘으면 여러 통으로 자동 분할됨)

이전에는 "오늘의 스케줄 안내"와 "순위 결과"를 서로 다른 두 통으로 나눠 보냈지만,
헷갈린다는 피드백에 따라 하나로 합쳤다. 전송은 src/kakao_sender.py가 카카오
REST API(OAuth refresh_token)를 통해 직접 처리하므로 Claude 세션 등 외부 개입
없이 완전히 무인으로 동작한다.
"""
from datetime import date

from config import EXCEL_PATH
from main_crawl import build_summary_chunks, fetch_group_ranks
from src.excel_writer import append_results
from src.kakao_sender import send_text_to_me
from src.schedule_logic import GOOGLE, engine_label_ko, get_today_group_and_engine


def main() -> None:
    today = date.today()
    group_and_engine = get_today_group_and_engine(today)
    if group_and_engine is None:
        print(f"{today}: 주말/공휴일이라 오늘은 실행하지 않습니다.")
        return
    group, engine = group_and_engine

    if engine != GOOGLE:
        # 네이버 플레이스 순위는 현재 신뢰할 수 있는 방법이 없어(공식 API는
        # 5위까지만 확인 가능, 비공식 스크래핑은 캡차 차단 위험) 카톡 전송을
        # 하지 않는다. 구글 날만 정상적으로 순위를 조회해 전송한다.
        print(f"{today}: {group}그룹 네이버 날 — 순위 알림을 보내지 않습니다.")
        return

    results = fetch_group_ranks(group, engine)
    append_results(EXCEL_PATH, today, group, engine_label_ko(engine), results)

    chunks = build_summary_chunks(today, group, engine, results)
    for chunk in chunks:
        send_text_to_me(chunk)
    print("\n\n".join(chunks))


if __name__ == "__main__":
    main()
