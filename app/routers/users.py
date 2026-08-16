"""
Users 라우터 (담당: 이다영) - 총 3개 엔드포인트.
확정 스키마 기준 users 테이블에는 email/created_at만 있고 프로필 수정 필드가 없으므로,
PATCH /me는 user_settings(high_contrast/font_size) 갱신으로 대응한다.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.user import UserRead, UserSettingsRead, UserSettingsUpdate

from app.crud import user as crud_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """
    내 프로필 조회:
    문지기(Depends)가 이미 유저 정보를 current_user에 담아줬기 때문에,
    DB를 뒤질 필요 없이 그냥 이 변수를 돌려주기만 하면 Pydantic이 예쁘게 포장해서 내보냅니다.
    """
    return current_user


@router.get("/me/settings", response_model=UserSettingsRead)
def get_my_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    내 설정 조회 (고대비/폰트크기/다크모드/프로필사진):
    한 번도 PATCH /users/me를 안 한 신규 유저도 기본값으로 조회 가능하도록
    없으면 만들어서 반환한다 (앱 시작 시 저장된 설정을 불러올 때 사용).
    """
    return crud_user.get_or_create_user_settings(db=db, user_id=current_user.id)


@router.patch("/me", response_model=UserSettingsRead)
def update_my_settings(
    payload: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    내 설정 변경 (무장애 UI 설정):
    앱에서 보낸 고대비/폰트크기 변경 요청(payload)을 CRUD 함수로 넘겨서 DB를 수정합니다.
    """
    updated_settings = crud_user.upsert_user_settings(db=db, user_id=current_user.id, update_data=payload)
    return updated_settings


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    crud_user.delete_user(db=db, user_id=current_user.id)
    return