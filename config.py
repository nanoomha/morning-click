"""프로젝트 전역 설정.

.env 파일에서 민감한 값(API 키 등)을 읽어오고, 나머지 고정값은 여기서 정의한다.
"""
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# 순위를 추적할 홈페이지 도메인 (구글 날 조회 대상)
HOMEPAGE_DOMAIN = "hearkorea.kr"

# 12개 지점을 3개씩 A/B/C/D 4개 그룹으로 나눠, 평일(공휴일 제외) 하루에 한
# 그룹씩 "구글 하루 → 네이버 하루" 순서로 순환 조회한다. 순서: A구글, A네이버,
# B구글, B네이버, C구글, C네이버, D구글, D네이버, 다시 A구글 ... (반복)
#
# - google_keyword: 구글 검색 시 사용할 검색어. hearkorea.kr 홈페이지가 이
#   검색어의 (광고 제외) 몇 번째에 나오는지 확인한다.
# - naver_keyword: 네이버 검색 시 사용할 검색어. 이 검색어로 네이버 플레이스
#   (지도)를 검색했을 때, 아래 naver_place_name 업체가 몇 번째에 나오는지
#   확인한다 (hearkorea.kr 웹사이트 순위가 아니라 네이버 플레이스 순위).
# - naver_place_name: 네이버 지도에 등록된 정확한 업체명.
LOCATIONS = [
    {
        "group": "A",
        "label": "일산",
        "google_keyword": "일산보청기",
        "naver_keyword": "일산보청기",
        "naver_place_name": "나눔보청기 일산점",
    },
    {
        "group": "A",
        "label": "인천부천",
        "google_keyword": "인천보청기",
        "naver_keyword": "부천보청기",
        "naver_place_name": "나눔보청기 인천부천점",
    },
    {
        "group": "A",
        "label": "분당",
        "google_keyword": "분당보청기",
        "naver_keyword": "분당보청기",
        "naver_place_name": "나눔보청기 분당점",
    },
    {
        "group": "B",
        "label": "대전",
        "google_keyword": "대전보청기",
        "naver_keyword": "대전보청기",
        "naver_place_name": "나눔보청기 대전점",
    },
    {
        "group": "B",
        "label": "광주",
        "google_keyword": "광주보청기",
        "naver_keyword": "광주보청기",
        "naver_place_name": "나눔보청기 광주점",
    },
    {
        "group": "B",
        "label": "대구",
        "google_keyword": "대구보청기",
        "naver_keyword": "대구보청기",
        "naver_place_name": "나눔보청기 대구점",
    },
    {
        "group": "C",
        "label": "부산서면",
        "google_keyword": "부산보청기",
        "naver_keyword": "부산보청기",
        "naver_place_name": "나눔보청기 서면점",
    },
    {
        "group": "C",
        "label": "부산사상",
        "google_keyword": "부산보청기",
        "naver_keyword": "부산보청기",
        "naver_place_name": "나눔보청기 사상점",
    },
    {
        "group": "C",
        "label": "울산",
        "google_keyword": "울산보청기",
        "naver_keyword": "울산보청기",
        "naver_place_name": "나눔보청기 울산점",
    },
    {
        "group": "D",
        "label": "종로",
        "google_keyword": "종로보청기",
        "naver_keyword": "종로보청기",
        "naver_place_name": "나눔보청기 종로점",
    },
    {
        "group": "D",
        "label": "강남",
        "google_keyword": "강남보청기",
        "naver_keyword": "강남보청기",
        "naver_place_name": "나눔보청기 강남점",
    },
    {
        "group": "D",
        "label": "수원",
        "google_keyword": "수원보청기",
        "naver_keyword": "수원보청기",
        "naver_place_name": "나눔보청기 수원점",
    },
]

# 그룹/엔진 순환 순서의 기준일. 2026-09-18(금)이 "A그룹 구글"이었다는 실측
# 기준으로 앵커를 잡는다. 이후 날짜는 이 날로부터 평일(공휴일 제외) 며칠째인지
# 세어 순서를 계산하므로, 특정 요일에 고정되지 않고 영업일 기준으로 계속
# 순환한다. src/schedule_logic.py 참고.
CYCLE_REFERENCE_DATE = date(2026, 9, 18)

# 순위 조회 시 확인할 최대 검색결과 개수 (이 안에서 못 찾으면 "미노출" 처리)
MAX_RESULTS_TO_CHECK = int(os.getenv("MAX_RESULTS_TO_CHECK", "50"))

# SerpApi (설정되어 있으면 구글 스크래핑 대신 API를 우선 사용)
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")

# Kakao "나에게 보내기"
KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY", "")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI", "https://localhost.com/oauth")
# 카카오 개발자 콘솔의 [카카오 로그인 > 보안]에서 Client Secret을 "사용함(필수)"로
# 설정한 경우에만 필요. 아니면 비워둔다.
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET", "")
KAKAO_TOKEN_FILE = BASE_DIR / "data" / "kakao_token.json"

# 결과 저장 Excel 파일
EXCEL_PATH = BASE_DIR / "data" / "rank_history.xlsx"

# 공통 HTTP 요청 헤더 (스크래핑 폴백에 사용)
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}

KAKAO_BOT_ID = "6aa89c3e872d86c4366afea7"
