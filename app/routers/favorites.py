from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud.favorite import (
    create_favorite,
    delete_favorite,
    get_facility_by_id,
    get_favorite_by_id,
    get_favorite_by_list_and_facility,
    get_favorite_list_by_id,
    get_favorite_lists_by_user,
    get_favorite_status,
    get_favorites_by_list,
)
from app.deps import get_current_user_mock
from app.models.user import User
from app.schemas.favorite import (
    FacilitySource,
    FavoriteCreate,
    FavoriteListRead,
    FavoriteRead,
    FavoriteStatusRead,
)


router = APIRouter(
    prefix="/favorites",
    tags=["favorites"],
)


def _require_internal_facility(db: Session, facility_id: str) -> None:
    """
    internal 소스만 UUID 형식 + 내부 DB 존재 여부를 검증한다. kakao 소스는 재조회 시
    카카오 API 쿼터가 소모되므로 검증 없이 프론트가 넘긴 값을 그대로 신뢰한다.
    """
    try:
        facility_uuid = UUID(facility_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="internal 시설의 facility_id는 UUID 형식이어야 합니다.",
        )

    facility = get_facility_by_id(
        db=db,
        facility_id=facility_uuid,
    )

    if facility is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="시설을 찾을 수 없습니다.",
        )


@router.get(
    "/lists",
    response_model=list[FavoriteListRead],
    status_code=status.HTTP_200_OK,
)
def read_favorite_lists(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_mock),
):
    """
    현재 사용자의 기본 즐겨찾기 목록 3개를 조회한다.

    - 즐겨찾은 곳
    - 가고 싶은 곳
    - 방문했던 곳
    """
    return get_favorite_lists_by_user(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/lists/{list_id}",
    response_model=list[FavoriteRead],
    status_code=status.HTTP_200_OK,
)
def read_favorites_in_list(
    list_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_mock),
):
    """
    특정 즐겨찾기 목록에 저장된 시설을 조회한다.
    """
    favorite_list = get_favorite_list_by_id(
        db=db,
        user_id=current_user.id,
        list_id=list_id,
    )

    if favorite_list is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="즐겨찾기 목록을 찾을 수 없습니다.",
        )

    return get_favorites_by_list(
        db=db,
        user_id=current_user.id,
        list_id=list_id,
    )


@router.post(
    "",
    response_model=FavoriteRead,
    status_code=status.HTTP_201_CREATED,
)
def add_favorite(
    payload: FavoriteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_mock),
):
    """
    시설을 선택한 기본 즐겨찾기 목록에 저장한다. facility_id는 내부 DB(source=internal,
    UUID)와 카카오 로컬 실시간 결과(source=kakao, place id 문자열) 둘 다 저장할 수 있다.
    """
    favorite_list = get_favorite_list_by_id(
        db=db,
        user_id=current_user.id,
        list_id=payload.list_id,
    )

    if favorite_list is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="즐겨찾기 목록을 찾을 수 없습니다.",
        )

    if payload.source == "internal":
        _require_internal_facility(db=db, facility_id=payload.facility_id)

    existing_favorite = get_favorite_by_list_and_facility(
        db=db,
        list_id=payload.list_id,
        facility_id=payload.facility_id,
        source=payload.source,
    )

    if existing_favorite is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="해당 시설은 이미 이 목록에 저장되어 있습니다.",
        )

    try:
        return create_favorite(
            db=db,
            user_id=current_user.id,
            list_id=payload.list_id,
            facility_id=payload.facility_id,
            source=payload.source,
        )

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="해당 시설은 이미 이 목록에 저장되어 있습니다.",
        )


@router.delete(
    "/{favorite_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_favorite(
    favorite_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_mock),
):
    """
    즐겨찾기 목록에 저장된 시설을 삭제한다.
    """
    favorite = get_favorite_by_id(
        db=db,
        user_id=current_user.id,
        favorite_id=favorite_id,
    )

    if favorite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="즐겨찾기 항목을 찾을 수 없습니다.",
        )

    delete_favorite(
        db=db,
        favorite=favorite,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


@router.get(
    "/status",
    response_model=FavoriteStatusRead,
    status_code=status.HTTP_200_OK,
)
def read_favorite_status(
    facility_id: str,
    source: FacilitySource = "internal",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_mock),
):
    """
    특정 시설이 어느 즐겨찾기 목록에 저장되어 있는지 조회한다.
    """
    if source == "internal":
        _require_internal_facility(db=db, facility_id=facility_id)

    favorite_list_ids = get_favorite_status(
        db=db,
        user_id=current_user.id,
        facility_id=facility_id,
        source=source,
    )

    return FavoriteStatusRead(
        is_favorite=len(favorite_list_ids) > 0,
        favorite_list_ids=favorite_list_ids,
    )
