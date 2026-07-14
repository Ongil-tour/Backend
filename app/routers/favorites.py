"""
Favorites 라우터 (담당: 신지민) - 총 5개 엔드포인트.
favorite_lists는 list_type만 갖는 3개 고정 리스트, favorites는 facility_id FK 참조로 정규화됨 (memory 기준).
DB 쓰기는 저장 시점에만 발생 (조회는 프론트 메모리 캐시 활용).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user_mock
from app.models.user import User
from app.schemas.favorite import FavoriteCreate, FavoriteRead, FavoriteListRead

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get("/lists", response_model=list[FavoriteListRead])
def get_my_favorite_lists(current_user: User = Depends(get_current_user_mock), db: Session = Depends(get_db)):
    """내 3개 고정 리스트 조회. TODO: 구현."""
    raise NotImplementedError


@router.get("/lists/{list_id}", response_model=list[FavoriteRead])
def get_favorite_list_items(list_id: int, current_user: User = Depends(get_current_user_mock), db: Session = Depends(get_db)):
    """특정 리스트에 담긴 시설 목록. TODO: 구현."""
    raise NotImplementedError


@router.post("", response_model=FavoriteRead)
def add_favorite(payload: FavoriteCreate, current_user: User = Depends(get_current_user_mock), db: Session = Depends(get_db)):
    """시설 저장. TODO: 구현."""
    raise NotImplementedError


@router.delete("/{favorite_id}")
def remove_favorite(favorite_id: int, current_user: User = Depends(get_current_user_mock), db: Session = Depends(get_db)):
    """저장 취소. TODO: 구현."""
    raise NotImplementedError


@router.get("/{facility_id}/status")
def check_favorite_status(facility_id: int, current_user: User = Depends(get_current_user_mock), db: Session = Depends(get_db)):
    """특정 시설이 내 리스트 중 어디에 저장되어 있는지 확인. TODO: 구현."""
    raise NotImplementedError