import uuid

from sqlalchemy.orm import Session

from app.models.favorite import FavoriteList, Favorite
from app.models.facility import Facility


def get_favorite_lists_by_user(
    db: Session,
    user_id: uuid.UUID,
) -> list[dict]:
    """특정 사용자의 즐겨찾기 목록과 목록별 저장 개수를 조회한다."""
    favorite_lists = (
        db.query(FavoriteList)
        .filter(FavoriteList.user_id == user_id)
        .order_by(FavoriteList.created_at.asc())
        .all()
    )

    result = []

    for favorite_list in favorite_lists:
        favorite_count = (
            db.query(Favorite)
            .filter(
                Favorite.list_id == favorite_list.id,
                Favorite.user_id == user_id,
            )
            .count()
        )

        result.append(
            {
                "id": favorite_list.id,
                "list_type": favorite_list.list_type,
                "favorite_count": favorite_count,
                "created_at": favorite_list.created_at,
            }
        )

    return result

def get_favorite_list_by_id(
    db: Session,
    user_id: uuid.UUID,
    list_id: uuid.UUID,
) -> FavoriteList | None:
    """현재 사용자가 소유한 특정 즐겨찾기 리스트를 조회한다."""
    return (
        db.query(FavoriteList)
        .filter(
            FavoriteList.id == list_id,
            FavoriteList.user_id == user_id,
        )
        .first()
    )


def get_favorites_by_list(
    db: Session,
    user_id: uuid.UUID,
    list_id: uuid.UUID,
) -> list[Favorite]:
    """특정 즐겨찾기 리스트에 저장된 항목을 조회한다."""
    return (
        db.query(Favorite)
        .filter(
            Favorite.list_id == list_id,
            Favorite.user_id == user_id,
        )
        .order_by(Favorite.created_at.desc())
        .all()
    )


def get_facility_by_id(
    db: Session,
    facility_id: uuid.UUID,
) -> Facility | None:
    """ID로 시설을 조회한다."""
    return (
        db.query(Facility)
        .filter(Facility.id == facility_id)
        .first()
    )


def get_existing_favorite(
    db: Session,
    list_id: uuid.UUID,
    facility_id: uuid.UUID,
) -> Favorite | None:
    """같은 리스트에 같은 시설이 이미 저장되어 있는지 확인한다."""
    return (
        db.query(Favorite)
        .filter(
            Favorite.list_id == list_id,
            Favorite.facility_id == facility_id,
        )
        .first()
    )


def create_favorite(
    db: Session,
    user_id: uuid.UUID,
    facility_id: uuid.UUID,
    list_id: uuid.UUID,
) -> Favorite:
    """즐겨찾기 항목을 생성한다."""
    favorite = Favorite(
        user_id=user_id,
        facility_id=facility_id,
        list_id=list_id,
    )

    db.add(favorite)
    db.commit()
    db.refresh(favorite)

    return favorite


def get_favorite_by_id(
    db: Session,
    user_id: uuid.UUID,
    favorite_id: uuid.UUID,
) -> Favorite | None:
    """현재 사용자의 즐겨찾기 항목을 ID로 조회한다."""
    return (
        db.query(Favorite)
        .filter(
            Favorite.id == favorite_id,
            Favorite.user_id == user_id,
        )
        .first()
    )


def delete_favorite(
    db: Session,
    favorite: Favorite,
) -> None:
    """즐겨찾기 항목을 삭제한다."""
    db.delete(favorite)
    db.commit()


def get_favorites_by_facility(
    db: Session,
    user_id: uuid.UUID,
    facility_id: uuid.UUID,
) -> list[Favorite]:
    """특정 시설에 대한 현재 사용자의 즐겨찾기 항목을 모두 조회한다."""
    return (
        db.query(Favorite)
        .filter(
            Favorite.user_id == user_id,
            Favorite.facility_id == facility_id,
        )
        .order_by(Favorite.list_id.asc())
        .all()
    )