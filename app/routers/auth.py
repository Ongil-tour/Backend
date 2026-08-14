"""
Auth 라우터 (담당: 이다영) - 총 3개 엔드포인트 확정.
소셜 로그인은 signup/login 구분 없이 provider callback 하나로 통일.
구글은 idToken 방식(프론트 SDK가 이미 로그인 완료), 카카오/네이버는 code 방식.
"""
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.deps import get_db
from app.schemas.user import TokenPair
from app.crud import auth as crud_auth
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from app.services.oauth import (
    verify_google_id_token,
    get_kakao_access_token, get_kakao_user_info,
    get_naver_access_token, get_naver_user_info,
)
from jose import JWTError

router = APIRouter(prefix="/auth", tags=["auth"])


class OAuthLoginRequest(BaseModel):
    code: Optional[str] = None       # 카카오/네이버 (기존 방식)
    id_token: Optional[str] = None   # 구글 (SDK가 이미 로그인 완료 후 발급한 idToken)


@router.post("/{provider}/callback", response_model=TokenPair)
async def oauth_callback(provider: str, payload: OAuthLoginRequest, db: Session = Depends(get_db)):
    """소셜 로그인. 구글은 idToken 검증, 카카오/네이버는 code 방식. 최초 로그인 시 회원가입까지 겸함."""
    if provider == "google":
        if not payload.id_token:
            raise HTTPException(status_code=422, detail="구글 로그인은 id_token이 필요합니다.")
        provider_user = await verify_google_id_token(payload.id_token)

    elif provider == "kakao":
        if not payload.code:
            raise HTTPException(status_code=422, detail="카카오 로그인은 code가 필요합니다.")
        provider_access_token = await get_kakao_access_token(payload.code)
        provider_user = await get_kakao_user_info(provider_access_token)

    elif provider == "naver":
        if not payload.code:
            raise HTTPException(status_code=422, detail="네이버 로그인은 code가 필요합니다.")
        provider_access_token = await get_naver_access_token(payload.code)
        provider_user = await get_naver_user_info(provider_access_token)

    else:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 provider: {provider}")

    # 이미 가입된 계정인지 확인 (이후 로직은 provider와 상관없이 공통)
    social_account = crud_auth.get_social_account(
        db, provider=provider, provider_user_id=provider_user["provider_user_id"]
    )

    if social_account:
        # 기존 유저 -> 로그인
        user_id = social_account.user_id
    else:
        # 처음 로그인하는 유저 -> 회원가입 겸용
        new_user = crud_auth.create_user_with_social_account(
            db,
            email=provider_user["email"],
            provider=provider,
            provider_user_id=provider_user["provider_user_id"],
        )
        user_id = new_user.id

    # 우리 서비스만의 JWT 발급
    access_token = create_access_token(user_id)
    refresh_token_str = create_refresh_token(user_id)

    # refresh token은 DB에 저장 (로그아웃 시 여기서 지움)
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    crud_auth.save_refresh_token(db, user_id=user_id, token=refresh_token_str, expires_at=expires_at)

    return TokenPair(access_token=access_token, refresh_token=refresh_token_str)


@router.post("/refresh", response_model=TokenPair)
def refresh_token(refresh_token: str = Body(..., embed=True), db: Session = Depends(get_db)):
    """rolling refresh token 재발급."""
    try:
        payload = decode_token(refresh_token)
    except JWTError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="refresh token이 아닙니다.")

    db_token = crud_auth.get_valid_refresh_token(db, refresh_token)
    if db_token is None:
        raise HTTPException(status_code=401, detail="만료되었거나 폐기된 토큰입니다.")

    user_id = db_token.user_id

    crud_auth.delete_refresh_token(db, refresh_token)

    new_access_token = create_access_token(user_id)
    new_refresh_token = create_refresh_token(user_id)
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    crud_auth.save_refresh_token(db, user_id=user_id, token=new_refresh_token, expires_at=expires_at)

    return TokenPair(access_token=new_access_token, refresh_token=new_refresh_token)


@router.post("/logout")
def logout(refresh_token: str = Body(..., embed=True), db: Session = Depends(get_db)):
    """refresh token 폐기."""
    crud_auth.delete_refresh_token(db, refresh_token)
    return {"detail": "로그아웃 되었습니다."}