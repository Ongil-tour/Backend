from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.favorite import (
    Favorite,
    FavoriteList,
)
from app.models.facility import Facility


def get_favorite_lists_by_user(
    db: Session,
    user_id: UUID,
) -> list[dict]:
    """
    현재 사용자의 모든 즐겨찾기 목록을 조회한다.
    각 목록에 저장된 즐겨찾기 개수도 함께 반환한다.
    """
    rows = (
        db.query(
            FavoriteList,
            func.count(Favorite.id).label("favorite_count"),
        )
        .outerjoin(
            Favorite,
            Favorite.list_id == FavoriteList.id,
        )
        .filter(
            FavoriteList.user_id == user_id,
        )
        .group_by(
            FavoriteList.id,
        )
        .order_by(
            FavoriteList.created_at.asc(),
        )
        .all()
    )

    return [
        {
            "id": favorite_list.id,
            "list_type": favorite_list.list_type,
            "created_at": favorite_list.created_at,
            "favorite_count": favorite_count,
        }
        for favorite_list, favorite_count in rows
    ]


def get_favorite_list_by_id(
    db: Session,
    user_id: UUID,
    list_id: UUID,
) -> FavoriteList | None:
    """
    현재 사용자가 소유한 특정 목록을 조회한다.
    """
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
    user_id: UUID,
    list_id: UUID,
) -> list[Favorite]:
    """
    특정 목록의 즐겨찾기 항목을 최신순으로 조회한다.
    """
    favorite_list = get_favorite_list_by_id(
        db=db,
        user_id=user_id,
        list_id=list_id,
    )

    if favorite_list is None:
        return []

    return (
        db.query(Favorite)
        .filter(
            Favorite.list_id == list_id,
        )
        .order_by(
            Favorite.created_at.desc(),
        )
        .all()
    )


def get_facility_by_id(
    db: Session,
    facility_id: UUID,
) -> Facility | None:
    """
    시설을 UUID로 조회한다.
    """
    return (
        db.query(Facility)
        .filter(
            Facility.id == facility_id,
        )
        .first()
    )


def get_favorite_by_id(
    db: Session,
    user_id: UUID,
    favorite_id: UUID,
) -> Favorite | None:
    """
    현재 사용자가 소유한 즐겨찾기 항목을 조회한다.
    """
    return (
        db.query(Favorite)
        .join(
            FavoriteList,
            Favorite.list_id == FavoriteList.id,
        )
        .filter(
            Favorite.id == favorite_id,
            FavoriteList.user_id == user_id,
        )
        .first()
    )


def get_favorite_by_list_and_facility(
    db: Session,
    list_id: UUID,
    facility_id: UUID,
) -> Favorite | None:
    """
    특정 목록에 특정 시설이 이미 저장되어 있는지 조회한다.

    list_id와 facility_id가 모두 일치하는 경우에만
    기존 즐겨찾기로 판단한다.
    """
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
    user_id: UUID,
    list_id: UUID,
    facility_id: UUID,
) -> Favorite:
    """
    현재 사용자의 즐겨찾기 목록에 시설을 저장한다.
    """
    favorite = Favorite(
        user_id=user_id,
        list_id=list_id,
        facility_id=facility_id,
    )

    db.add(favorite)
    db.commit()
    db.refresh(favorite)

    return favorite


def delete_favorite(
    db: Session,
    favorite: Favorite,
) -> None:
    """
    즐겨찾기 항목을 삭제한다.
    """
    db.delete(favorite)
    db.commit()


def get_favorite_status(
    db: Session,
    user_id: UUID,
    facility_id: UUID,
) -> list[UUID]:
    """
    해당 시설이 저장된 현재 사용자의 목록 ID를 반환한다.
    """
    rows = (
        db.query(Favorite.list_id)
        .join(
            FavoriteList,
            Favorite.list_id == FavoriteList.id,
        )
        .filter(
            FavoriteList.user_id == user_id,
            Favorite.facility_id == facility_id,
        )
        .all()
    )

    return [
        row.list_id
        for row in rows
    ]