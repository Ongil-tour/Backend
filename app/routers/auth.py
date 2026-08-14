"""
Auth 라우터 (담당: 이다영) - 총 3개 엔드포인트 확정.
소셜 로그인은 signup/login 구분 없이 provider callback 하나로 통일.
"""
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.deps import get_db
from app.schemas.user import TokenPair
from app.crud import auth as crud_auth
from app.crud.user import get_user_by_email
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from app.services.oauth import (
    get_google_access_token, get_google_user_info,
    get_kakao_access_token, get_kakao_user_info,
    get_naver_access_token, get_naver_user_info,
)
from jose import JWTError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/{provider}/callback", response_model=TokenPair)
async def oauth_callback(provider: str, code: str, db: Session = Depends(get_db)):
    """카카오/구글/네이버 OAuth 콜백. 최초 로그인 시 회원가입까지 겸함."""
    # 1. provider별로 다른 방식으로 code -> access token -> 사용자 정보 획득
    if provider == "google":
        provider_access_token = await get_google_access_token(code)
        provider_user = await get_google_user_info(provider_access_token)
    elif provider == "kakao":
        provider_access_token = await get_kakao_access_token(code)
        provider_user = await get_kakao_user_info(provider_access_token)
    elif provider == "naver":
        provider_access_token = await get_naver_access_token(code)
        provider_user = await get_naver_user_info(provider_access_token)
    else:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 provider: {provider}")

    # 2. 이미 가입된 계정인지 확인 (이후 로직은 provider와 상관없이 공통)
    social_account = crud_auth.get_social_account(
        db, provider=provider, provider_user_id=provider_user["provider_user_id"]
    )

    if social_account:
        # 기존 유저 -> 로그인
        user_id = social_account.user_id
    else:
        existing_user = get_user_by_email(db, email=provider_user["email"])

        if existing_user:
            # 다른 provider로 이미 가입된 이메일 -> 새 User를 또 만들지 않고 계정만 연동
            # (users.email이 unique라서 그냥 새로 만들면 500이 남)
            crud_auth.link_social_account(
                db,
                user_id=existing_user.id,
                provider=provider,
                provider_user_id=provider_user["provider_user_id"],
            )
            user_id = existing_user.id
        else:
            # 처음 로그인하는 유저 -> 회원가입 겸용
            new_user = crud_auth.create_user_with_social_account(
                db,
                email=provider_user["email"],
                provider=provider,
                provider_user_id=provider_user["provider_user_id"],
            )
            user_id = new_user.id

    # 3. 우리 서비스만의 JWT 발급
    access_token = create_access_token(user_id)
    refresh_token_str = create_refresh_token(user_id)

    # 4. refresh token은 DB에 저장 (로그아웃 시 여기서 지움)
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    crud_auth.save_refresh_token(db, user_id=user_id, token=refresh_token_str, expires_at=expires_at)

    return TokenPair(access_token=access_token, refresh_token=refresh_token_str)


@router.post("/refresh", response_model=TokenPair)
def refresh_token(refresh_token: str = Body(..., embed=True), db: Session = Depends(get_db)):
    """rolling refresh token 재발급."""
    # 1. JWT 자체가 유효한지 확인 (서명 위조/만료 여부)
    try:
        payload = decode_token(refresh_token)
    except JWTError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="refresh token이 아닙니다.")

    # 2. DB에도 살아있는 토큰인지 확인 (로그아웃해서 지워진 건 아닌지)
    db_token = crud_auth.get_valid_refresh_token(db, refresh_token)
    if db_token is None:
        raise HTTPException(status_code=401, detail="만료되었거나 폐기된 토큰입니다.")

    user_id = db_token.user_id

    # 3. rolling 방식: 기존 토큰은 폐기하고 새로 발급
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