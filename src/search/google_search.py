"""구글 검색 순위(광고 제외) 조회.

우선순위:
1. SERPAPI_KEY가 설정되어 있으면 SerpApi를 사용한다. SerpApi는 광고(organic_results
   에서 제외)와 순위를 명확히 구분해서 제공하므로 훨씬 안정적이다.
2. 설정되어 있지 않으면 requests + BeautifulSoup으로 google.com을 직접 스크래핑한다.
   이 방식은 무료이지만 구글의 HTML 구조가 수시로 바뀌고, 반복 요청 시 캡차로
   차단될 수 있어 완전한 안정성을 보장하지 않는다. 장기적으로는 SerpApi 사용을
   권장한다.
"""
from typing import Optional

import requests
from bs4 import BeautifulSoup

from config import DEFAULT_HEADERS, SERPAPI_KEY
from src.search.base import SearchBlockedError, is_target_domain


def search_rank(keyword: str, target_domain: str, max_results: int = 50) -> Optional[int]:
    if SERPAPI_KEY:
        return _rank_via_serpapi(keyword, target_domain, max_results)
    return _rank_via_scraping(keyword, target_domain, max_results)


def _rank_via_serpapi(keyword: str, target_domain: str, max_results: int) -> Optional[int]:
    params = {
        "engine": "google",
        "q": keyword,
        "google_domain": "google.co.kr",
        "gl": "kr",
        "hl": "ko",
        "num": max_results,
        "api_key": SERPAPI_KEY,
    }
    resp = requests.get("https://serpapi.com/search", params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    if "error" in data:
        raise RuntimeError(f"SerpApi 오류: {data['error']}")

    for item in data.get("organic_results", []):
        link = item.get("link", "")
        if link and is_target_domain(link, target_domain):
            return item.get("position")
    return None


def _rank_via_scraping(keyword: str, target_domain: str, max_results: int) -> Optional[int]:
    params = {
        "q": keyword,
        "num": max_results,
        "hl": "ko",
        "gl": "kr",
    }
    resp = requests.get(
        "https://www.google.com/search",
        params=params,
        headers=DEFAULT_HEADERS,
        timeout=15,
    )
    resp.raise_for_status()

    lowered = resp.text.lower()
    if "unusual traffic" in lowered or "recaptcha" in lowered:
        raise SearchBlockedError(
            "구글이 자동화된 요청을 차단했습니다(캡차). SERPAPI_KEY 설정을 권장합니다."
        )

    soup = BeautifulSoup(resp.text, "html.parser")
    search_root = soup.select_one("#search") or soup

    # 구글은 HTML 구조를 수시로 바꾸므로 여러 후보 선택자를 순서대로 시도한다.
    result_blocks = search_root.select("div.g") or search_root.select(
        "div[data-hveid] div.yuRUbf, div[data-hveid] div.tF2Cxc"
    )

    rank = 0
    for block in result_blocks:
        link_tag = block.select_one("a[href^='http']")
        if not link_tag:
            continue
        href = link_tag.get("href", "")
        rank += 1
        if is_target_domain(href, target_domain):
            return rank
        if rank >= max_results:
            break
    return None
