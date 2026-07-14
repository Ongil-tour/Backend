"""
Auth 라우터 (담당: 이다영) - 총 3개 엔드포인트 확정.
소셜 로그인은 signup/login 구분 없이 provider callback 하나로 통일.
아래는 merge 순서(auth-users 우선)를 위한 스텁이며, 실제 로직은 담당자가 채운다.
"""
from fastapi import APIRouter

from app.schemas.user import TokenPair

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/{provider}/callback", response_model=TokenPair)
def oauth_callback(provider: str, code: str):
    """카카오/구글/네이버 OAuth 콜백. 최초 로그인 시 회원가입까지 겸함. TODO: 구현."""
    raise NotImplementedError


@router.post("/refresh", response_model=TokenPair)
def refresh_token(refresh_token: str):
    """rolling refresh token 재발급. TODO: 구현."""
    raise NotImplementedError


@router.post("/logout")
def logout():
    """refresh token 폐기(Redis/DB). TODO: 구현."""
    raise NotImplementedError