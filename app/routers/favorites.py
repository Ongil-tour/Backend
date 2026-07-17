"""
Favorites 라우터 (담당: 신지민) - 총 5개 엔드포인트.
favorite_lists는 list_type만 갖는 3개 고정 리스트, favorites는 facility_id FK 참조로 정규화됨 (memory 기준).
DB 쓰기는 저장 시점에만 발생 (조회는 프론트 메모리 캐시 활용).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud import favorite as favorite_crud
from app.deps import get_current_user_mock
from app.models.user import User
from app.schemas.favorite import FavoriteCreate, FavoriteRead, FavoriteListRead

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get(
    "/lists",
    response_model=list[FavoriteListRead],
    summary="내 즐겨찾기 목록 조회",
)
def get_my_favorite_lists(
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    """현재 사용자의 고정 즐겨찾기 목록 3개를 조회한다."""
    return favorite_crud.get_favorite_lists_by_user(
        db=db,
        user_id=current_user.id,
    )

@router.get(
    "/lists/{list_id}",
    response_model=list[FavoriteRead],
    summary="특정 즐겨찾기 리스트 항목 조회",
)
def get_favorite_list_items(
    list_id: int,
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    """현재 사용자가 소유한 특정 리스트의 즐겨찾기 항목을 조회한다."""

    favorite_list = favorite_crud.get_favorite_list_by_id(
        db=db,
        user_id=current_user.id,
        list_id=list_id,
    )

    if favorite_list is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="즐겨찾기 리스트를 찾을 수 없습니다.",
        )

    return favorite_crud.get_favorites_by_list(
        db=db,
        user_id=current_user.id,
        list_id=list_id,
    )
@router.post(
    "",
    response_model=FavoriteRead,
    status_code=status.HTTP_201_CREATED,
    summary="즐겨찾기 추가",
)
def add_favorite(
    payload: FavoriteCreate,
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    """시설을 현재 사용자의 특정 즐겨찾기 리스트에 저장한다."""

    favorite_list = favorite_crud.get_favorite_list_by_id(
        db=db,
        user_id=current_user.id,
        list_id=payload.favorite_list_id,
    )

    if favorite_list is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="즐겨찾기 리스트를 찾을 수 없습니다.",
        )

    facility = favorite_crud.get_facility_by_id(
        db=db,
        facility_id=payload.facility_id,
    )

    if facility is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="시설을 찾을 수 없습니다.",
        )

    existing_favorite = favorite_crud.get_existing_favorite(
        db=db,
        favorite_list_id=payload.favorite_list_id,
        facility_id=payload.facility_id,
    )

    if existing_favorite is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 해당 리스트에 저장된 시설입니다.",
        )

    return favorite_crud.create_favorite(
        db=db,
        user_id=current_user.id,
        facility_id=payload.facility_id,
        favorite_list_id=payload.favorite_list_id,
    )
@router.delete(
    "/{favorite_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="즐겨찾기 삭제",
)
def remove_favorite(
    favorite_id: int,
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    """현재 사용자의 즐겨찾기 항목을 삭제한다."""

    favorite = favorite_crud.get_favorite_by_id(
        db=db,
        user_id=current_user.id,
        favorite_id=favorite_id,
    )

    if favorite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="즐겨찾기를 찾을 수 없습니다.",
        )

    favorite_crud.delete_favorite(
        db=db,
        favorite=favorite,
    )

    return None

@router.get(
    "/{facility_id}/status",
    summary="시설 즐겨찾기 상태 확인",
)
def check_favorite_status(
    facility_id: int,
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    """특정 시설이 현재 사용자의 어느 리스트에 저장되어 있는지 확인한다."""

    facility = favorite_crud.get_facility_by_id(
        db=db,
        facility_id=facility_id,
    )

    if facility is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="시설을 찾을 수 없습니다.",
        )

    favorites = favorite_crud.get_favorites_by_facility(
        db=db,
        user_id=current_user.id,
        facility_id=facility_id,
    )

    return {
        "is_favorite": len(favorites) > 0,
        "favorite_list_ids": [
            favorite.favorite_list_id
            for favorite in favorites
        ],
    }