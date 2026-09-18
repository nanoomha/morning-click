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
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from bs4 import BeautifulSoup

from config import SERPAPI_KEY
from src.search.base import SearchBlockedError, is_target_domain


def _unwrap_google_redirect(href: str) -> str:
    """구글이 링크를 '/url?q=실제주소&...' 형태(절대/상대 경로 모두 가능)로
    감싸서 내려줄 때가 있다. 이 경우 href의 도메인은 항상 google.com(또는
    비어있음)이 되어 대상 도메인과 절대 매칭되지 않으므로, q(또는 url) 쿼리
    파라미터 안의 실제 주소를 꺼내 써야 한다.
    """
    parsed = urlparse(href)
    is_google_redirect = parsed.path == "/url" and (not parsed.netloc or "google." in parsed.netloc)
    if is_google_redirect:
        query_params = parse_qs(parsed.query)
        for key in ("q", "url"):
            if query_params.get(key):
                return query_params[key][0]
    return href


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
        "device": "mobile",
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


# 실제 고객은 대부분 모바일로 검색하므로, SerpApi(device=mobile)와 동일하게
# Selenium 폴백도 모바일 화면/UA로 렌더링해 순위 기준을 맞춘다.
MOBILE_USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
)


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
    options.add_experimental_option(
        "mobileEmulation",
        {
            "deviceMetrics": {"width": 412, "height": 915, "pixelRatio": 2.625},
            "userAgent": MOBILE_USER_AGENT,
        },
    )
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

        # 구글은 결과를 감싸는 div의 class를 수시로 바꾸지만(div.g 등), 각 결과의
        # 제목은 거의 항상 <h3> 태그로 되어 있어 이를 기준으로 찾는 편이 훨씬
        # 안정적이다. h3를 포함한 링크(<a>)를 문서 순서대로(=노출 순서대로) 모은다.
        anchors = search_root.select("a:has(h3)")

        rank = 0
        for anchor in anchors:
            href = _unwrap_google_redirect(anchor.get("href", ""))
            if not href.startswith("http"):
                continue
            rank += 1
            if is_target_domain(href, target_domain):
                return rank
            if rank >= max_results:
                break
        return None
    finally:
        driver.quit()
