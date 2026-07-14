"""
Users 라우터 (담당: 이다영) - 총 3개 엔드포인트.
"""
from fastapi import APIRouter, Depends

from app.deps import get_current_user_mock
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def get_my_profile(current_user: User = Depends(get_current_user_mock)):
    """TODO: 구현."""
    raise NotImplementedError


@router.patch("/me", response_model=UserRead)
def update_my_profile(payload: UserUpdate, current_user: User = Depends(get_current_user_mock)):
    """TODO: 구현."""
    raise NotImplementedError


@router.delete("/me")
def withdraw(current_user: User = Depends(get_current_user_mock)):
    """회원 탈퇴. TODO: 구현."""
    raise NotImplementedError