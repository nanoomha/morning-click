"""네이버 플레이스(지도) 순위 조회.

네이버는 '플레이스 순위 조회'를 위한 공식 오픈 API를 제공하지 않는다. 이 모듈은
네이버 지도(map.naver.com)가 내부적으로 사용하는 검색 API를 그대로 호출한다.
이 API는 비공식(reverse-engineered)이라 네이버가 예고 없이 응답 구조를 바꾸면
이 코드도 깨질 수 있다 — 실제 배포 후 첫 실행 결과를 꼭 확인하고, 파싱이 안 되면
아래 _extract_place_list()의 응답 구조 가정을 실제 응답에 맞게 고쳐야 한다.

순위는 hearkorea.kr 같은 URL이 아니라, 네이버 지도에 등록된 업체명(상호명)으로
찾는다. 비슷한 이름의 다른 업체와 헷갈릴 수 있으므로, 정확한 상호명을
config.py의 LOCATIONS에 등록해두어야 한다.
"""
from typing import List, Optional

import requests

from config import DEFAULT_HEADERS
from src.search.base import SearchBlockedError

SEARCH_URL = "https://map.naver.com/p/api/search/allSearch"

HEADERS = {
    "User-Agent": DEFAULT_HEADERS["User-Agent"],
    "Referer": "https://map.naver.com/",
    "Accept": "application/json, text/plain, */*",
}


def fetch_place_names(keyword: str, max_results: int = 50) -> List[str]:
    """주어진 검색어로 네이버 플레이스를 검색해, 노출 순서대로 업체명 목록을 반환한다."""
    resp = requests.get(
        SEARCH_URL,
        params={"query": keyword, "type": "all", "searchCoord": "", "page": 1},
        headers=HEADERS,
        timeout=15,
    )
    resp.raise_for_status()

    lowered = resp.text.lower()
    if "captcha" in lowered:
        raise SearchBlockedError("네이버가 자동화된 요청을 차단했습니다(캡차).")

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
