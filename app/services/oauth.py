"""
소셜 로그인(OAuth) 연동 - 구글 / 카카오 / 네이버.

프론트가 카카오/네이버도 구글과 동일하게 각 provider 네이티브 SDK로 로그인을
끝내고 SDK가 발급한 토큰(구글=idToken, 카카오/네이버=accessToken)을 그대로
넘겨주는 방식으로 확정됨 -> 백엔드는 인가 코드 교환(code -> access token) 없이
provider에게 토큰 검증 + 사용자 정보(email) 조회만 한다.
프론트가 인가 코드 흐름을 안 타서 state/PKCE도 프론트 책임에서 빠짐.
"""
import os

import httpx
from fastapi import HTTPException

# ── 구글 ──────────────────────────────
# idToken의 aud claim이 이 값과 같은지 검증해서 다른 앱용 토큰 도용을 막는다.
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")


# ============================================================
# 구글
# ============================================================

async def verify_google_id_token(id_token: str) -> dict:
    """
    프론트(모바일 SDK)가 이미 로그인 완료 후 받은 구글 idToken을 검증하고,
    안에 담긴 사용자 정보(email 등)를 꺼냄.
    """
    verify_url = "https://oauth2.googleapis.com/tokeninfo"

    async with httpx.AsyncClient() as client:
        response = await client.get(verify_url, params={"id_token": id_token})

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="유효하지 않은 구글 idToken입니다.")

    payload = response.json()

    # 이 idToken이 진짜 우리 앱을 위해 발급된 게 맞는지 확인 (다른 앱용 토큰 도용 방지)
    if payload.get("aud") != GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=401, detail="이 앱을 위해 발급된 토큰이 아닙니다.")

    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="구글 계정에서 이메일을 가져올 수 없습니다.")

    return {
        "provider_user_id": payload["sub"],  # 구글의 고유 사용자 ID
        "email": email,
    }

# ============================================================
# 카카오
# ============================================================

async def get_kakao_user_info(kakao_access_token: str) -> dict:
    """카카오 access token으로 사용자 정보(email) 조회."""
    user_info_url = "https://kapi.kakao.com/v2/user/me"
    headers = {"Authorization": f"Bearer {kakao_access_token}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(user_info_url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="카카오 사용자 정보 조회 실패")

    user_data = response.json()
    kakao_account = user_data.get("kakao_account", {})
    email = kakao_account.get("email")

    if not email:
        raise HTTPException(status_code=400, detail="카카오 계정에서 이메일을 가져올 수 없습니다.")

    return {
        "provider_user_id": str(user_data["id"]),
        "email": email,
    }


# ============================================================
# 네이버
# ============================================================

async def get_naver_user_info(naver_access_token: str) -> dict:
    """네이버 access token으로 사용자 정보(email) 조회."""
    user_info_url = "https://openapi.naver.com/v1/nid/me"
    headers = {"Authorization": f"Bearer {naver_access_token}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(user_info_url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="네이버 사용자 정보 조회 실패")

    user_data = response.json()
    response_data = user_data.get("response", {})
    email = response_data.get("email")

    if not email:
        raise HTTPException(status_code=400, detail="네이버 계정에서 이메일을 가져올 수 없습니다.")

    return {
        "provider_user_id": response_data["id"],
        "email": email,
    }