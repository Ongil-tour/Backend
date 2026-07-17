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
from app.schemas.favorite import (
    FavoriteCreate,
    FavoriteListRead,
    FavoriteRead,
    FavoriteStatusRead,
)
router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get(
    "/lists",
    response_model=list[FavoriteListRead],
    status_code=status.HTTP_200_OK,
    summary="내 즐겨찾기 목록 조회",
    description="현재 사용자의 고정 즐겨찾기 목록 3개를 조회합니다.",
)
def get_my_favorite_lists(
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    return favorite_crud.get_favorite_lists_by_user(
        db=db,
        user_id=current_user.id,
    )
@router.get(
    "/lists/{list_id}",
    response_model=list[FavoriteRead],
    status_code=status.HTTP_200_OK,
    summary="특정 즐겨찾기 리스트 조회",
    description="현재 사용자의 특정 즐겨찾기 리스트에 저장된 항목을 조회합니다.",
    responses={
        404: {
            "description": "즐겨찾기 리스트를 찾을 수 없음",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "즐겨찾기 리스트를 찾을 수 없습니다."
                    }
                }
            },
        }
    },
)
def get_favorite_list_items(
    list_id: int,
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
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
    description="시설을 현재 사용자의 특정 즐겨찾기 리스트에 추가합니다.",
    responses={
        404: {
            "description": "시설 또는 즐겨찾기 리스트를 찾을 수 없음"
        },
        409: {
            "description": "같은 리스트에 이미 저장된 시설",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "이미 해당 리스트에 저장된 시설입니다."
                    }
                }
            },
        },
    },
)
def add_favorite(
    payload: FavoriteCreate,
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    ...
@router.delete(
    "/{favorite_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="즐겨찾기 삭제",
    description="현재 사용자의 즐겨찾기 항목을 삭제합니다.",
    responses={
        404: {
            "description": "즐겨찾기 항목을 찾을 수 없음",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "즐겨찾기를 찾을 수 없습니다."
                    }
                }
            },
        }
    },
)
def remove_favorite(
    favorite_id: int,
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    ...
@router.get(
    "/{facility_id}/status",
    response_model=FavoriteStatusRead,
    status_code=status.HTTP_200_OK,
    summary="시설 즐겨찾기 상태 조회",
    description="특정 시설이 현재 사용자의 어느 즐겨찾기 리스트에 저장되어 있는지 확인합니다.",
    responses={
        404: {
            "description": "시설을 찾을 수 없음",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "시설을 찾을 수 없습니다."
                    }
                }
            },
        }
    },
)
def check_favorite_status(
    facility_id: int,
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    ...