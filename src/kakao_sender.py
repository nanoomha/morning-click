"""카카오톡 "나에게 보내기" 알림 전송.

최초 1회 kakao_auth_setup.py 를 실행해 access_token / refresh_token을 발급받아
KAKAO_TOKEN_FILE에 저장해두어야 한다. 이후에는 refresh_token으로 access_token을
자동 갱신하여 메시지를 전송한다.
"""
import json

import requests

from config import KAKAO_CLIENT_SECRET, KAKAO_REST_API_KEY, KAKAO_TOKEN_FILE

TOKEN_URL = "https://kauth.kakao.com/oauth/token"
SEND_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"


class KakaoNotConfiguredError(RuntimeError):
    """카카오 토큰이 아직 발급되지 않았을 때 발생시키는 예외."""


def _load_tokens() -> dict:
    if not KAKAO_TOKEN_FILE.exists():
        raise KakaoNotConfiguredError(
            f"{KAKAO_TOKEN_FILE} 파일이 없습니다. 먼저 kakao_auth_setup.py를 실행해 "
            "카카오 로그인 인증을 완료하세요."
        )
    return json.loads(KAKAO_TOKEN_FILE.read_text(encoding="utf-8"))


def _save_tokens(tokens: dict) -> None:
    KAKAO_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    KAKAO_TOKEN_FILE.write_text(json.dumps(tokens, ensure_ascii=False, indent=2), encoding="utf-8")


def _refresh_access_token(tokens: dict) -> dict:
    token_data = {
        "grant_type": "refresh_token",
        "client_id": KAKAO_REST_API_KEY,
        "refresh_token": tokens["refresh_token"],
    }
    if KAKAO_CLIENT_SECRET:
        token_data["client_secret"] = KAKAO_CLIENT_SECRET

    resp = requests.post(TOKEN_URL, data=token_data, timeout=15)
    resp.raise_for_status()
    new_tokens = resp.json()

    tokens["access_token"] = new_tokens["access_token"]
    # 카카오는 refresh_token 유효기간이 얼마 안 남았을 때만 새 refresh_token을 내려준다.
    if "refresh_token" in new_tokens:
        tokens["refresh_token"] = new_tokens["refresh_token"]

    _save_tokens(tokens)
    return tokens


def send_text_to_me(message: str) -> None:
    """카카오톡 '나에게 보내기'로 텍스트 메시지를 전송한다."""
    tokens = _load_tokens()
    tokens = _refresh_access_token(tokens)

    template_object = {
        "object_type": "text",
        "text": message,
        "link": {"web_url": "https://hearkorea.kr", "mobile_web_url": "https://hearkorea.kr"},
    }

    resp = requests.post(
        SEND_URL,
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        data={"template_object": json.dumps(template_object, ensure_ascii=False)},
        timeout=15,
    )
    resp.raise_for_status()
    result = resp.json()
    if result.get("result_code") != 0:
        raise RuntimeError(f"카카오톡 전송 실패: {result}")
