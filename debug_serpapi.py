"""SerpApi가 실제로 몇 개의 결과를 돌려주는지, hearkorea.kr이 어떤 링크
형태로 나오는지 확인하기 위한 진단용 스크립트. 문제 해결 후 삭제해도 된다.

사용법: python debug_serpapi.py 인천보청기
"""
import sys

import requests

from config import SERPAPI_KEY

keyword = sys.argv[1] if len(sys.argv) > 1 else "인천보청기"

if not SERPAPI_KEY:
    raise SystemExit(".env에 SERPAPI_KEY가 없습니다.")

params = {
    "engine": "google",
    "q": keyword,
    "google_domain": "google.co.kr",
    "gl": "kr",
    "hl": "ko",
    "device": "mobile",
    "num": 50,
    "api_key": SERPAPI_KEY,
}
resp = requests.get("https://serpapi.com/search", params=params, timeout=20)
resp.raise_for_status()
data = resp.json()

if "error" in data:
    print("SerpApi 오류:", data["error"])
    raise SystemExit(1)

organic = data.get("organic_results", [])
print(f"검색어: {keyword}")
print(f"organic_results 개수: {len(organic)}")
print()
for item in organic:
    print(f"{item.get('position')}. {item.get('link')}")

hearkorea_hits = [item for item in organic if "hearkorea.kr" in (item.get("link") or "")]
print()
print("hearkorea.kr 포함된 결과:", hearkorea_hits if hearkorea_hits else "없음")
