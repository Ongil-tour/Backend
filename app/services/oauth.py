"""
구글 OAuth 연동.
- code를 구글 access token으로 교환
- 그 토큰으로 구글 사용자 정보(email) 조회
"""
import os

import httpx
from fastapi import HTTPException

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "")


async def get_google_access_token(code: str) -> str:
    """구글이 준 code를 구글 access token으로 교환."""
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,   # 카카오와 다르게 구글은 필수
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "code": code,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=payload)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="구글 토큰 교환 실패")

    token_data = response.json()
    return token_data["access_token"]


async def get_google_user_info(google_access_token: str) -> dict:
    """구글 access token으로 사용자 정보(email) 조회."""
    user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {"Authorization": f"Bearer {google_access_token}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(user_info_url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="구글 사용자 정보 조회 실패")

    user_data = response.json()
    email = user_data.get("email")

    if not email:
        raise HTTPException(status_code=400, detail="구글 계정에서 이메일을 가져올 수 없습니다.")

    return {
        "provider_user_id": user_data["id"],  # 구글의 고유 사용자 ID
        "email": email,
    }