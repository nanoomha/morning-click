"""프로젝트 전역 설정.

.env 파일에서 민감한 값(API 키 등)을 읽어오고, 나머지 고정값은 여기서 정의한다.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# 순위를 추적할 홈페이지 도메인
HOMEPAGE_DOMAIN = "hearkorea.kr"

# 순위를 추적할 12개 키워드
KEYWORDS = [
    "종로보청기",
    "강남보청기",
    "수원보청기",
    "일산보청기",
    "인천보청기",
    "분당보청기",
    "대전보청기",
    "광주보청기",
    "대구보청기",
    "부산보청기(서면)",
    "부산보청기(사상)",
    "울산보청기",
]

# 순위 조회 시 확인할 최대 검색결과 개수 (이 안에서 못 찾으면 "미노출" 처리)
MAX_RESULTS_TO_CHECK = int(os.getenv("MAX_RESULTS_TO_CHECK", "50"))

# Naver 오픈 API (설정되어 있으면 스크래핑 대신 API를 우선 사용)
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")

# SerpApi (설정되어 있으면 스크래핑 대신 API를 우선 사용)
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
