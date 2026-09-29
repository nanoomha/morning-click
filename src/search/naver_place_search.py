"""네이버 플레이스(지도) 순위 조회.

우선순위:
1. NAVER_CLIENT_ID / NAVER_CLIENT_SECRET이 설정되어 있으면 네이버 오픈 API의
   지역 검색(local) API를 사용한다. 이건 공식 API라 캡차 차단을 받지 않고
   안정적이지만, 한 번에 최대 5개 업체까지만 반환한다는 제약이 있다(네이버
   지역 검색 API 자체의 한계). 즉 5위 밖은 "미노출"로 나온다.
   (발급: https://developers.naver.com/apps/#/register, "검색" API 사용 설정 필요)
2. 설정되어 있지 않으면, 네이버 지도(map.naver.com)가 내부적으로 쓰는 비공식
   검색 API를 그대로 호출한다. 더 깊은 순위까지 볼 수 있지만, 네이버가 예고
   없이 응답 구조를 바꾸거나 캡차로 차단할 수 있어 안정성이 떨어진다.

순위는 hearkorea.kr 같은 URL이 아니라, 네이버 지도에 등록된 업체명(상호명)으로
찾는다. 비슷한 이름의 다른 업체와 헷갈릴 수 있으므로, 정확한 상호명을
config.py의 LOCATIONS에 등록해두어야 한다.
"""
import re
from typing import List, Optional

import requests

from config import NAVER_CLIENT_ID, NAVER_CLIENT_SECRET
from src.search.base import SearchBlockedError

SEARCH_URL = "https://map.naver.com/p/api/search/allSearch"
LOCAL_API_URL = "https://openapi.naver.com/v1/search/local.json"
LOCAL_API_MAX_DISPLAY = 5  # 네이버 지역 검색 API 자체의 상한

# 실제 고객은 대부분 모바일로 검색하므로, 구글 조회와 마찬가지로 모바일
# User-Agent로 요청한다 (네이버 플레이스 순위 자체는 위치/평판 기반이라
# PC/모바일 차이가 구글 organic 검색만큼 크지는 않지만, 기준은 통일해둔다).
MOBILE_USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
)

HEADERS = {
    "User-Agent": MOBILE_USER_AGENT,
    "Referer": "https://m.map.naver.com/",
    "Accept": "application/json, text/plain, */*",
}

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def fetch_place_names(keyword: str, max_results: int = 50) -> List[str]:
    """주어진 검색어로 네이버 플레이스를 검색해, 노출 순서대로 업체명 목록을 반환한다."""
    if NAVER_CLIENT_ID and NAVER_CLIENT_SECRET:
        return _fetch_via_official_api(keyword, max_results)
    return _fetch_via_scraping(keyword, max_results)


def _fetch_via_official_api(keyword: str, max_results: int) -> List[str]:
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    display = min(max(max_results, 1), LOCAL_API_MAX_DISPLAY)
    resp = requests.get(
        LOCAL_API_URL,
        params={"query": keyword, "display": display},
        headers=headers,
        timeout=15,
    )
    resp.raise_for_status()
    items = resp.json().get("items", [])
    # title에 <b>강조태그</b>가 섞여 오므로 제거한다.
    return [_HTML_TAG_RE.sub("", item.get("title", "")) for item in items]


def _fetch_via_scraping(keyword: str, max_results: int) -> List[str]:
    resp = requests.get(
        SEARCH_URL,
        params={"query": keyword, "type": "all", "searchCoord": "", "page": 1},
        headers=HEADERS,
        timeout=15,
    )
    resp.raise_for_status()

    lowered = resp.text.lower()
    if "captcha" in lowered:
        raise SearchBlockedError(
            "네이버가 자동화된 요청을 차단했습니다(캡차). NAVER_CLIENT_ID/SECRET 설정을 권장합니다."
        )

    try:
        data = resp.json()
    except ValueError as exc:
        raise RuntimeError(
            f"네이버 플레이스 응답이 JSON이 아닙니다. 응답 구조가 바뀐 것으로 보입니다.\n"
            f"응답 앞부분: {resp.text[:500]}"
        ) from exc

    names = _extract_place_names(data)
    if names is None:
        raise RuntimeError(
            "네이버 플레이스 응답에서 업체 목록을 찾지 못했습니다. 응답 구조가 바뀐 "
            f"것으로 보입니다. 실제 응답을 확인해 _extract_place_names()를 고쳐야 합니다.\n"
            f"응답 원문(앞부분): {str(data)[:800]}"
        )
    return names[:max_results]


def _extract_place_names(data: dict) -> Optional[List[str]]:
    """네이버 지도 검색 API 응답에서 업체명 목록을 순서대로 추출한다.

    알려진 응답 형태(result.place.list[].name)를 우선 시도하고, 구조가 다르면
    None을 반환해 호출부에서 명확한 에러로 알 수 있게 한다.
    """
    try:
        items = data["result"]["place"]["list"]
    except (KeyError, TypeError):
        items = None

    if items is None:
        return None

    names = []
    for item in items:
        name = item.get("name") or item.get("title") or ""
        if name:
            names.append(name)
    return names


def find_rank_by_name(place_names: List[str], target_name: str) -> Optional[int]:
    """업체명 목록에서 target_name과 일치(부분 포함)하는 첫 항목의 순위(1부터)를 찾는다."""
    for idx, name in enumerate(place_names, start=1):
        if target_name in name or name in target_name:
            return idx
    return None


def search_place_rank(keyword: str, place_name: str, max_results: int = 50) -> Optional[int]:
    """keyword로 네이버 플레이스를 검색했을 때 place_name 업체의 순위를 반환한다."""
    place_names = fetch_place_names(keyword, max_results)
    return find_rank_by_name(place_names, place_name)
