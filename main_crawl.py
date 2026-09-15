"""오전 10시: 오늘의 검색엔진으로 12개 키워드 순위를 조회하고,
   Excel에 기록한 뒤 결과 메시지를 표준출력으로 내보낸다.

카카오톡 전송은 이 스크립트가 직접 하지 않는다. Play MCP의 KakaotalkChat-MemoChat은
MCP 도구라서 Claude(에이전트) 세션 안에서만 호출할 수 있고, Windows 작업 스케줄러가
띄우는 독립 python.exe 프로세스에서는 호출할 수 없기 때문이다. 대신 이 스크립트는
결과 메시지를 표준출력(stdout)에 "그 한 줄/블록만" 깔끔하게 출력하고, 이를 실행한
Claude 세션이 그 출력을 그대로 읽어 MemoChat(message=...)을 호출해 전송한다.
진단/경고 로그는 표준오류(stderr)로 보내 stdout이 메시지로만 채워지도록 한다.
"""
import sys
import traceback
from datetime import date
from typing import List, Optional, Tuple

from config import EXCEL_PATH, HOMEPAGE_DOMAIN, KEYWORDS, MAX_RESULTS_TO_CHECK
from src.excel_writer import append_results
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


MEMOCHAT_CHAR_LIMIT = 200
# Claude 세션이 stdout에서 메시지 여러 개를 정확히 구분해 각각 MemoChat으로
# 보낼 수 있도록 쓰는 구분자. 메시지 본문에는 나타나지 않는 문자열이어야 한다.
MEMOCHAT_MESSAGE_SEPARATOR = "\n<<<MEMOCHAT_SPLIT>>>\n"


def build_summary_chunks(
    today: date,
    engine: str,
    results: List[Tuple[str, Optional[int]]],
    limit: int = MEMOCHAT_CHAR_LIMIT,
) -> List[str]:
    """결과를 MemoChat 글자수 제한(기본 200자) 안에 들어가도록 여러 메시지로 나눈다.

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
    print(MEMOCHAT_MESSAGE_SEPARATOR.join(chunks))


if __name__ == "__main__":
    main()
