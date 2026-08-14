"""
공통 의존성.
get_current_user(): Authorization: Bearer <access_token> 헤더를 검증해서 현재 유저를 반환.
                     app.core.security.decode_token으로 서명/만료를 확인하고,
                     payload의 sub(user_id)로 실제 DB 유저를 조회한다.
"""
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.crud.user import get_user_by_id
from app.models.user import User

# 로컬 seed(app/scripts/seed.py)가 만드는 더미 유저 ID.
# 테스트에서 이 ID로 진짜 access token을 발급받아 인증 헤더로 사용한다.
MOCK_USER_ID = uuid.UUID(
    "00000000-0000-0000-0000-000000000001"
)

# auto_error=False로 두고 직접 401을 던져서 에러 메시지/헤더를 통일한다.
bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise _unauthorized("인증이 필요합니다.")

    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise _unauthorized("유효하지 않거나 만료된 토큰입니다.")

    if payload.get("type") != "access":
        raise _unauthorized("access token이 아닙니다.")

    try:
        user_id = uuid.UUID(payload.get("sub", ""))
    except (ValueError, TypeError):
        raise _unauthorized("유효하지 않은 토큰입니다.")

    user = get_user_by_id(db, user_id)

    if user is None:
        raise _unauthorized("존재하지 않는 사용자입니다.")

    return user
