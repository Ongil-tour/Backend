"""
Auth 관련 CRUD 함수.
- social_accounts: 소셜 로그인 계정 조회/생성
- refresh_tokens: 토큰 저장/조회/삭제
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.favorite import FavoriteList, ListType
from app.models.user import User, SocialAccount, RefreshToken


# ── social_accounts 관련 ──────────────────────────────

def get_social_account(db: Session, provider: str, provider_user_id: str):
    """
    provider(예: 'kakao')와 provider_user_id(카카오가 알려준 그 사람 고유번호)로
    이미 가입된 소셜 계정이 있는지 찾음. 없으면 None 반환.
    """
    return (
        db.query(SocialAccount)
        .filter(
            SocialAccount.provider == provider,
            SocialAccount.provider_user_id == provider_user_id,
        )
        .first()
    )


def create_user_with_social_account(
    db: Session, email: str | None, provider: str, provider_user_id: str
):
    """
    최초 로그인(=회원가입)일 때 호출.
    users 테이블에 유저를 만들고, social_accounts 연결 정보와
    고정 즐겨찾기 목록(FREQUENT/WISHLIST/VISITED) 3개도 함께 만듦
    (favorites 파트가 가정하는 "가입 시 리스트 3개 자동 생성"을 여기서 보장).
    """
    # 1. 유저 생성
    new_user = User(email=email)
    db.add(new_user)
    db.flush()  # 아직 commit은 안 하지만, new_user.id를 미리 만들어서 쓸 수 있게 해줌

    # 2. 소셜 계정 연결 정보 생성
    new_social_account = SocialAccount(
        user_id=new_user.id,
        provider=provider,
        provider_user_id=provider_user_id,
    )
    db.add(new_social_account)

    # 3. 고정 즐겨찾기 목록 3종 생성
    for list_type in ListType:
        db.add(FavoriteList(user_id=new_user.id, list_type=list_type.value))

    db.commit()
    db.refresh(new_user)
    return new_user


def link_social_account(
    db: Session, user_id: uuid.UUID, provider: str, provider_user_id: str
) -> SocialAccount:
    """
    이미 다른 provider로 가입된 이메일로 로그인한 경우 호출.
    새 User/즐겨찾기 목록을 만들지 않고, 기존 유저에 이 provider 계정만 연결한다.
    (users.email이 unique라서 그냥 새 User를 만들면 IntegrityError가 남)
    """
    new_social_account = SocialAccount(
        user_id=user_id,
        provider=provider,
        provider_user_id=provider_user_id,
    )
    db.add(new_social_account)
    db.commit()
    db.refresh(new_social_account)
    return new_social_account


# ── refresh_tokens 관련 ──────────────────────────────

def save_refresh_token(
    db: Session, user_id: uuid.UUID, token: str, expires_at: datetime
):
    """새로 발급한 refresh token을 DB에 저장."""
    db_token = RefreshToken(user_id=user_id, token=token, expires_at=expires_at)
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token


def get_valid_refresh_token(db: Session, token: str):
    """
    토큰 문자열로 DB에서 찾되, 만료 시각이 지났으면 없는 것처럼 None 반환.
    (JWT 자체 만료 검사와는 별개로, DB에도 만료 시각을 저장해서 이중으로 확인하는 것)
    """
    db_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()
    if db_token is None:
        return None
    if db_token.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        return None
    return db_token


def delete_refresh_token(db: Session, token: str):
    """로그아웃 시 refresh token을 DB에서 삭제 (즉시 무효화)."""
    db.query(RefreshToken).filter(RefreshToken.token == token).delete()
    db.commit()