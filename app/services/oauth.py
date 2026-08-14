"""
소셜 로그인(OAuth) 연동 - 구글 / 카카오 / 네이버.
각 provider별로 code -> access token 교환, access token -> 사용자 정보(email) 조회를 담당.
"""
import os

import httpx
from fastapi import HTTPException

# ── 구글 ──────────────────────────────
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "")

# ── 카카오 ──────────────────────────────
KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY", "")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET", "")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI", "")

# ── 네이버 ──────────────────────────────
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")
NAVER_REDIRECT_URI = os.getenv("NAVER_REDIRECT_URI", "")


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

async def get_kakao_access_token(code: str) -> str:
    """카카오가 준 code를 카카오 access token으로 교환."""
    token_url = "https://kauth.kakao.com/oauth/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": KAKAO_REST_API_KEY,
        "redirect_uri": KAKAO_REDIRECT_URI,
        "code": code,
        "client_secret": KAKAO_CLIENT_SECRET, 
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=payload, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="카카오 토큰 교환 실패")

    return response.json()["access_token"]


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

async def get_naver_access_token(code: str) -> str:
    """네이버가 준 code를 네이버 access token으로 교환."""
    token_url = "https://nid.naver.com/oauth2.0/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": NAVER_CLIENT_ID,
        "client_secret": NAVER_CLIENT_SECRET,
        "redirect_uri": NAVER_REDIRECT_URI,
        "code": code,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, params=payload)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="네이버 토큰 교환 실패")

    token_data = response.json()

    # 네이버는 에러여도 200을 주고 body의 error 필드로만 알려주는 경우가 있어 별도 체크
    if "access_token" not in token_data:
        raise HTTPException(status_code=400, detail="네이버 토큰 교환 실패")

    return token_data["access_token"]


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