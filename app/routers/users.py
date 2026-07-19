"""
Users 라우터 (담당: 이다영) - 총 3개 엔드포인트.
확정 스키마 기준 users 테이블에는 email/created_at만 있고 프로필 수정 필드가 없으므로,
PATCH /me는 user_settings(high_contrast/font_size) 갱신으로 대응한다.
"""
from fastapi import APIRouter, Depends

from app.deps import get_current_user_mock
from app.models.user import User
from app.schemas.user import UserRead, UserSettingsRead, UserSettingsUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def get_my_profile(current_user: User = Depends(get_current_user_mock)):
    """TODO: 구현."""
    raise NotImplementedError


@router.patch("/me", response_model=UserSettingsRead)
def update_my_settings(payload: UserSettingsUpdate, current_user: User = Depends(get_current_user_mock)):
    """TODO: 구현."""
    raise NotImplementedError


@router.delete("/me")
def withdraw(current_user: User = Depends(get_current_user_mock)):
    """회원 탈퇴. TODO: 구현."""
    raise NotImplementedError