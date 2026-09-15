"""구글 검색 순위(광고 제외) 조회.

우선순위:
1. SERPAPI_KEY가 설정되어 있으면 SerpApi를 사용한다. SerpApi는 광고(organic_results
   에서 제외)와 순위를 명확히 구분해서 제공하므로 가장 안정적이다.
2. 설정되어 있지 않으면 Selenium(헤드리스 Chrome)으로 google.com을 직접 렌더링해
   스크래핑한다. 단순 requests 방식은 구글이 JS 없이 요청하는 트래픽을 봇으로
   간주해 차단(캡차)하는 경우가 많아, 실제 브라우저처럼 동작하는 Selenium을
   사용한다. 다만 이 방식도 구글의 HTML 구조 변경이나 반복 요청에 따른 차단
   가능성은 남아 있어, 장기적으로는 SerpApi 사용을 권장한다.
   Selenium 4.6+ 는 Selenium Manager를 내장하고 있어 별도로 chromedriver를
   설치하지 않아도 되지만, 로컬에 Google Chrome이 설치되어 있어야 한다.
"""
from typing import Optional
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

from config import DEFAULT_HEADERS, SERPAPI_KEY
from src.search.base import SearchBlockedError, is_target_domain


def search_rank(keyword: str, target_domain: str, max_results: int = 50) -> Optional[int]:
    if SERPAPI_KEY:
        return _rank_via_serpapi(keyword, target_domain, max_results)
    return _rank_via_selenium(keyword, target_domain, max_results)


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


def _build_chrome_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--lang=ko-KR")
    options.add_argument(f"user-agent={DEFAULT_HEADERS['User-Agent']}")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    return webdriver.Chrome(options=options)


def _rank_via_selenium(keyword: str, target_domain: str, max_results: int) -> Optional[int]:
    query = urlencode({"q": keyword, "num": max_results, "hl": "ko", "gl": "kr"})
    url = f"https://www.google.com/search?{query}"

    driver = _build_chrome_driver()
    try:
        driver.set_page_load_timeout(30)
        driver.get(url)

        page_source = driver.page_source
        lowered = page_source.lower()
        if "unusual traffic" in lowered or "recaptcha" in lowered:
            raise SearchBlockedError(
                "구글이 자동화된 요청을 차단했습니다(캡차). SERPAPI_KEY 설정을 권장합니다."
            )

        soup = BeautifulSoup(page_source, "html.parser")
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
    finally:
        driver.quit()
