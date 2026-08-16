"""
공통 의존성.
get_current_user_mock(): 이다영의 JWT 미들웨어(Week 2)가 나오기 전까지
                         이가희/신지민이 인증에 막히지 않고 개발하기 위한 임시 mock.
                         실 인증 붙으면 get_current_user로 교체하고 이 함수는 삭제.
get_current_user(): 실제 JWT 인증. Authorization: Bearer <access_token> 헤더를
                    검증해서 진짜 로그인한 유저를 반환.
"""
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User

MOCK_USER_ID = uuid.UUID(
    "00000000-0000-0000-0000-000000000001"
)

bearer_scheme = HTTPBearer()


def get_current_user_mock(
    db: Session = Depends(get_db),
) -> User:
    user = db.get(User, MOCK_USER_ID)

    if user is None:
        raise RuntimeError(
            f"mock user({MOCK_USER_ID})가 DB에 없습니다. "
            "로컬 seed로 더미 유저를 먼저 생성하세요."
        )

    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    요청 헤더의 Authorization: Bearer <access_token>을 검증하고,
    그 안에 담긴 유저 ID로 실제 유저를 조회해서 반환.
    """
    token = credentials.credentials

    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="access token이 아닙니다.",
        )

    user_id = payload.get("sub")
    user = db.get(User, uuid.UUID(user_id))

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="존재하지 않는 유저입니다.",
        )

    return user