"""
JWT(JSON Web Token) 생성/검증 유틸리티.
로그인한 유저를 식별하기 위한 '증표'를 만들고 확인하는 역할을 함.
"""
import uuid
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError

from app.core.config import settings

# app.core.config.settings가 .env를 읽는 유일한 창구.
# 여기서 os.getenv()로 따로 읽으면 설정값이 두 곳으로 갈라져서 어긋날 수 있음.
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM

ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


def create_access_token(user_id: uuid.UUID) -> str:
    """유저 ID를 받아서 access token(짧은 수명)을 만들어 반환."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: uuid.UUID) -> str:
    """유저 ID를 받아서 refresh token(긴 수명)을 만들어 반환."""
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """
    토큰 문자열을 검증하고 payload를 꺼내줌.
    서명이 위조됐거나 만료됐으면 JWTError 예외가 발생함
    -> 이건 auth.py에서 잡아서 401 에러로 바꿔줄 예정 (다음 단계에서 다룰게요).
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])