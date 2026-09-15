"""네이버 검색 순위(광고 제외) 조회.

우선순위:
1. NAVER_CLIENT_ID / NAVER_CLIENT_SECRET이 설정되어 있으면 네이버 오픈 API의
   웹문서 검색(webkr)을 사용한다. 이 API는 파워링크 등 광고를 포함하지 않고
   순수 웹문서 검색 결과만 순서대로 반환하므로 가장 안정적이다.
   (발급: https://developers.naver.com/apps/#/register)
2. 설정되어 있지 않으면 requests + BeautifulSoup으로 search.naver.com을 직접
   스크래핑한다. 네이버는 파워링크(광고) 영역과 통합웹 결과 영역의 HTML 구조를
   자주 변경하므로, 이 방식은 완전한 안정성을 보장하지 않는다. 장기적으로는
   오픈 API 사용을 권장한다.
"""
from typing import Optional

import requests
from bs4 import BeautifulSoup

from config import DEFAULT_HEADERS, NAVER_CLIENT_ID, NAVER_CLIENT_SECRET
from src.search.base import is_target_domain


def search_rank(keyword: str, target_domain: str, max_results: int = 50) -> Optional[int]:
    if NAVER_CLIENT_ID and NAVER_CLIENT_SECRET:
        return _rank_via_api(keyword, target_domain, max_results)
    return _rank_via_scraping(keyword, target_domain, max_results)


def _rank_via_api(keyword: str, target_domain: str, max_results: int) -> Optional[int]:
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    # webkr(웹문서) API는 display 최대 100까지 지원한다.
    display = min(max(max_results, 1), 100)
    resp = requests.get(
        "https://openapi.naver.com/v1/search/webkr.json",
        params={"query": keyword, "display": display},
        headers=headers,
        timeout=15,
    )
    resp.raise_for_status()
    items = resp.json().get("items", [])

    for idx, item in enumerate(items[:max_results], start=1):
        link = item.get("link", "")
        if link and is_target_domain(link, target_domain):
            return idx
    return None


def _rank_via_scraping(keyword: str, target_domain: str, max_results: int) -> Optional[int]:
    resp = requests.get(
        "https://search.naver.com/search.naver",
        params={"query": keyword, "where": "web"},
        headers=DEFAULT_HEADERS,
        timeout=15,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    rank = 0
    for item in soup.select("li.bx"):
        # 파워링크(광고) 등 스폰서 영역에 속한 결과는 제외한다.
        if item.find_parent(id="power_link") or item.select_one(".ad_dsp, .lnk_txt_ad"):
            continue

        link_tag = item.select_one(
            "a.link_tit, a.total_tit, div.total_wrap a, a.api_txt_lines"
        )
        if not link_tag or not link_tag.get("href"):
            continue

        href = link_tag["href"]
        rank += 1
        if is_target_domain(href, target_domain):
            return rank
        if rank >= max_results:
            break
    return None
