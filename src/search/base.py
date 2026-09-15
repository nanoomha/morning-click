"""검색 순위 조회 공통 유틸리티."""
from urllib.parse import urlparse


def extract_domain(url: str) -> str:
    """URL에서 'www.' 를 제거한 순수 도메인을 추출한다."""
    netloc = urlparse(url).netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc


def is_target_domain(url: str, target_domain: str) -> bool:
    """url의 도메인이 target_domain과 동일하거나 그 서브도메인인지 확인한다.

    단순 substring 매칭(`target_domain in url`)은 예를 들어
    'fake-hearkorea.kr.evil.com' 같은 도메인도 잘못 매칭될 수 있어 사용하지 않는다.
    """
    domain = extract_domain(url)
    target = target_domain.lower()
    return domain == target or domain.endswith("." + target)


class SearchBlockedError(RuntimeError):
    """검색엔진이 자동화된 요청을 차단(캡차 등)했을 때 발생시키는 예외."""
