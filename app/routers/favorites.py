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

from app.crud.favorite import (
    create_custom_favorite_list,
    create_favorite,
    delete_custom_favorite_list,
    delete_favorite,
    get_facility_by_id,
    get_favorite_by_id,
    get_favorite_by_list_and_facility,
    get_favorite_list_by_id,
    get_favorite_list_by_name,
    get_favorite_lists_by_user,
    get_favorite_status,
    get_favorites_by_list,
    update_custom_favorite_list,
)
from app.core.database import get_db
from app.deps import get_current_user_mock
from app.models.favorite import ListType
from app.models.user import User
from app.schemas.favorite import (
    FavoriteCreate,
    FavoriteListCreate,
    FavoriteListRead,
    FavoriteListUpdate,
    FavoriteRead,
    FavoriteStatusRead,
)


router = APIRouter(
    prefix="/favorites",
    tags=["favorites"],
)


@router.get(
    "/lists",
    response_model=list[FavoriteListRead],
    status_code=status.HTTP_200_OK,
)
def read_favorite_lists(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user_mock
    ),
):
    """
    현재 사용자의 기본 목록과 사용자 지정 목록을 모두 조회한다.
    """
    return get_favorite_lists_by_user(
        db=db,
        user_id=current_user.id,
    )


@router.post(
    "/lists",
    response_model=FavoriteListRead,
    status_code=status.HTTP_201_CREATED,
)
def create_favorite_list(
    payload: FavoriteListCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user_mock
    ),
):
    """
    사용자 지정 즐겨찾기 목록을 생성한다.
    """
    name = payload.name.strip()

    existing_list = get_favorite_list_by_name(
        db=db,
        user_id=current_user.id,
        name=name,
    )

    if existing_list is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "같은 이름의 즐겨찾기 목록이 "
                "이미 존재합니다."
            ),
        )

    try:
        favorite_list = create_custom_favorite_list(
            db=db,
            user_id=current_user.id,
            name=name,
        )

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "같은 이름의 즐겨찾기 목록이 "
                "이미 존재합니다."
            ),
        )

    return {
        "id": favorite_list.id,
        "list_type": favorite_list.list_type,
        "name": favorite_list.name,
        "created_at": favorite_list.created_at,
        "favorite_count": 0,
    }


@router.get(
    "/lists/{list_id}",
    response_model=list[FavoriteRead],
    status_code=status.HTTP_200_OK,
)
def read_favorites_in_list(
    list_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user_mock
    ),
):
    """
    특정 즐겨찾기 목록에 들어 있는 항목을 조회한다.
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


@router.patch(
    "/lists/{list_id}",
    response_model=FavoriteListRead,
    status_code=status.HTTP_200_OK,
)
def update_favorite_list(
    list_id: UUID,
    payload: FavoriteListUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user_mock
    ),
):
    """
    사용자 지정 즐겨찾기 목록 이름을 변경한다.
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

    if favorite_list.list_type != ListType.CUSTOM:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="기본 즐겨찾기 목록은 수정할 수 없습니다.",
        )

    new_name = payload.name.strip()

    duplicate_list = get_favorite_list_by_name(
        db=db,
        user_id=current_user.id,
        name=new_name,
    )

    if (
        duplicate_list is not None
        and duplicate_list.id != favorite_list.id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "같은 이름의 즐겨찾기 목록이 "
                "이미 존재합니다."
            ),
        )

    try:
        updated_list = update_custom_favorite_list(
            db=db,
            favorite_list=favorite_list,
            name=new_name,
        )

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "같은 이름의 즐겨찾기 목록이 "
                "이미 존재합니다."
            ),
        )

    return {
        "id": updated_list.id,
        "list_type": updated_list.list_type,
        "name": updated_list.name,
        "created_at": updated_list.created_at,
        "favorite_count": len(updated_list.favorites),
    }


@router.delete(
    "/lists/{list_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_favorite_list(
    list_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user_mock
    ),
):
    """
    사용자 지정 즐겨찾기 목록을 삭제한다.

    기본 목록은 삭제할 수 없다.
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

    if favorite_list.list_type != ListType.CUSTOM:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="기본 즐겨찾기 목록은 삭제할 수 없습니다.",
        )

    delete_custom_favorite_list(
        db=db,
        favorite_list=favorite_list,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
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
    시설을 특정 즐겨찾기 목록에 저장한다.
    """

    # 1. 현재 사용자가 소유한 목록인지 확인
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

    # 2. 실제로 존재하는 시설인지 확인
    facility = get_facility_by_id(
        db=db,
        facility_id=payload.facility_id,
    )

    if facility is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="시설을 찾을 수 없습니다.",
        )

    # 3. 같은 목록에 같은 시설이 이미 저장됐는지 확인
    existing_favorite = get_favorite_by_list_and_facility(
        db=db,
        list_id=payload.list_id,
        facility_id=payload.facility_id,
    )

    # 조회 결과가 실제로 존재할 때만 409
    if existing_favorite is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="해당 시설은 이미 이 목록에 저장되어 있습니다.",
        )

    # 4. 새 즐겨찾기 저장
    try:
        favorite = create_favorite(
            db=db,
            user_id=current_user.id,
            list_id=payload.list_id,
            facility_id=payload.facility_id,
    )
        return favorite
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
    current_user: User = Depends(
        get_current_user_mock
    ),
):
    """
    즐겨찾기 항목을 삭제한다.
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
        status_code=status.HTTP_204_NO_CONTENT
    )


@router.get(
    "/status",
    response_model=FavoriteStatusRead,
    status_code=status.HTTP_200_OK,
)
def read_favorite_status(
    facility_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user_mock
    ),
):
    """
    특정 시설이 즐겨찾기에 저장되어 있는지 조회한다.
    """
    facility = get_facility_by_id(
        db=db,
        facility_id=facility_id,
    )

    if facility is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="시설을 찾을 수 없습니다.",
        )

    favorite_list_ids = get_favorite_status(
        db=db,
        user_id=current_user.id,
        facility_id=facility_id,
    )

    return FavoriteStatusRead(
        is_favorite=len(favorite_list_ids) > 0,
        favorite_list_ids=favorite_list_ids,
    )