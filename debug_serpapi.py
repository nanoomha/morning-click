"""SerpApi 조회가 실제로 몇 페이지까지 가져오는지, hearkorea.kr을 몇 위에서
찾는지 확인하기 위한 진단용 스크립트. 문제 해결 후 삭제해도 된다.

사용법: python debug_serpapi.py 인천보청기
"""
import sys

import requests

from config import HOMEPAGE_DOMAIN, MAX_RESULTS_TO_CHECK, SERPAPI_KEY
from src.search.base import is_target_domain
from src.search.google_search import search_rank

keyword = sys.argv[1] if len(sys.argv) > 1 else "인천보청기"

if not SERPAPI_KEY:
    raise SystemExit(".env에 SERPAPI_KEY가 없습니다.")

print(f"검색어: {keyword} / 조회 범위: 1~{MAX_RESULTS_TO_CHECK}위\n")

rank = 0
start = 0
found_at = None
while rank < MAX_RESULTS_TO_CHECK:
    params = {
        "engine": "google",
        "q": keyword,
        "google_domain": "google.co.kr",
        "gl": "kr",
        "hl": "ko",
        "device": "mobile",
        "start": start,
        "api_key": SERPAPI_KEY,
    }
    resp = requests.get("https://serpapi.com/search", params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    if "error" in data:
        print("SerpApi 오류:", data["error"])
        raise SystemExit(1)

    organic = data.get("organic_results", [])
    print(f"--- start={start} (이번 페이지 {len(organic)}개) ---")
    if not organic:
        print("(더 이상 결과 없음)")
        break

    for item in organic:
        rank += 1
        link = item.get("link", "")
        marker = " <-- 매치!" if is_target_domain(link, HOMEPAGE_DOMAIN) else ""
        print(f"{rank}. {link}{marker}")
        if marker and found_at is None:
            found_at = rank
        if rank >= MAX_RESULTS_TO_CHECK:
            break

    start += len(organic)

print()
print("최종 결과:", f"{found_at}위" if found_at else "미노출")
print("(search_rank() 실제 호출 결과:", search_rank(keyword, HOMEPAGE_DOMAIN, MAX_RESULTS_TO_CHECK), ")")
