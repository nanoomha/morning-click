"""카카오톡 '나에게 보내기' 최초 1회 인증 설정 스크립트.

사용법:
    1. https://developers.kakao.com 에서 애플리케이션을 생성한다.
    2. [카카오 로그인] 활성화, Redirect URI에 .env의 KAKAO_REDIRECT_URI 값과
       동일한 값을 등록한다 (기본값: https://localhost.com/oauth).
    3. [카카오 로그인 > 동의항목]에서 "카카오톡 메시지 전송"(talk_message) 항목을
       사용 설정한다.
    4. [내 애플리케이션 > 앱 키]의 REST API 키를 .env의 KAKAO_REST_API_KEY에 넣는다.
    5. 이 스크립트를 실행하고 안내에 따라 인증을 완료한다.
"""
import json
from urllib.parse import parse_qs, urlparse

import requests

from config import KAKAO_REDIRECT_URI, KAKAO_REST_API_KEY, KAKAO_TOKEN_FILE

AUTHORIZE_URL = "https://kauth.kakao.com/oauth/authorize"
TOKEN_URL = "https://kauth.kakao.com/oauth/token"


def main() -> None:
    if not KAKAO_REST_API_KEY:
        raise SystemExit(".env 파일에 KAKAO_REST_API_KEY를 먼저 설정하세요.")

    auth_url = (
        f"{AUTHORIZE_URL}?client_id={KAKAO_REST_API_KEY}"
        f"&redirect_uri={KAKAO_REDIRECT_URI}&response_type=code"
        f"&scope=talk_message"
    )

    print("아래 URL을 브라우저에 열어 카카오 로그인 및 동의를 진행하세요:\n")
    print(auth_url)
    print(
        "\n로그인 후 리디렉션된 주소창의 URL을 그대로 복사해 아래에 붙여넣거나, "
        "code= 뒤의 값만 입력해도 됩니다."
    )
    raw = input("\n리디렉션된 URL 또는 code 값 입력: ").strip()

    code = raw
    if raw.startswith("http"):
        parsed = urlparse(raw)
        params = parse_qs(parsed.query)
        if "code" not in params:
            raise SystemExit("URL에서 code 파라미터를 찾지 못했습니다.")
        code = params["code"][0]

    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "client_id": KAKAO_REST_API_KEY,
            "redirect_uri": KAKAO_REDIRECT_URI,
            "code": code,
        },
        timeout=15,
    )
    resp.raise_for_status()
    tokens = resp.json()

    if "access_token" not in tokens:
        raise SystemExit(f"토큰 발급 실패: {tokens}")

    KAKAO_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    KAKAO_TOKEN_FILE.write_text(json.dumps(tokens, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n토큰이 {KAKAO_TOKEN_FILE} 에 저장되었습니다. 이제 알림을 사용할 수 있습니다.")


if __name__ == "__main__":
    main()
