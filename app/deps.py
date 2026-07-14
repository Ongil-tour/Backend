"""
공통 의존성.
get_current_user_mock(): 이다영의 JWT 미들웨어(Week 2)가 나오기 전까지
                         이가희/신지민이 인증에 막히지 않고 개발하기 위한 임시 mock.
                         실 인증 붙으면 get_current_user로 교체하고 이 함수는 삭제.
"""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User


def get_current_user_mock(db: Session = Depends(get_db)) -> User:
    """
    TODO(실 인증 연동 후 제거): 항상 id=1 사용자를 반환.
    로컬 개발 시 users 테이블에 id=1 더미 유저를 미리 넣어둘 것 (seed 스크립트 또는 수동 insert).
    """
    user = db.get(User, 1)
    if user is None:
        raise RuntimeError(
            "mock user(id=1)가 DB에 없습니다. 로컬 seed로 더미 유저를 먼저 생성하세요."
        )
    return user


# 실 인증 완료 후 아래로 교체 예정:
# def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
#     ...