from sqlalchemy.orm import Session

from app.models.favorite import Favorite, FavoriteList
from app.models.facility import Facility


def get_favorite_lists(
    db: Session,
    user_id: int,
) -> list[FavoriteList]:
    return (
        db.query(FavoriteList)
        .filter(FavoriteList.user_id == user_id)
        .order_by(FavoriteList.id)
        .all()
    )


def get_favorite_list_by_id(
    db: Session,
    user_id: int,
    favorite_list_id: int,
) -> FavoriteList | None:
    return (
        db.query(FavoriteList)
        .filter(
            FavoriteList.id == favorite_list_id,
            FavoriteList.user_id == user_id,
        )
        .first()
    )


def get_facility_by_id(
    db: Session,
    facility_id: int,
) -> Facility | None:
    return (
        db.query(Facility)
        .filter(Facility.id == facility_id)
        .first()
    )


def get_favorites_by_list(
    db: Session,
    user_id: int,
    favorite_list_id: int,
) -> list[Favorite]:
    return (
        db.query(Favorite)
        .filter(
            Favorite.user_id == user_id,
            Favorite.favorite_list_id == favorite_list_id,
        )
        .order_by(Favorite.created_at.desc())
        .all()
    )


def get_existing_favorite(
    db: Session,
    favorite_list_id: int,
    facility_id: int,
) -> Favorite | None:
    return (
        db.query(Favorite)
        .filter(
            Favorite.favorite_list_id == favorite_list_id,
            Favorite.facility_id == facility_id,
        )
        .first()
    )


def get_favorite_by_id(
    db: Session,
    user_id: int,
    favorite_id: int,
) -> Favorite | None:
    return (
        db.query(Favorite)
        .filter(
            Favorite.id == favorite_id,
            Favorite.user_id == user_id,
        )
        .first()
    )


def create_favorite(
    db: Session,
    user_id: int,
    facility_id: int,
    favorite_list_id: int,
) -> Favorite:
    favorite = Favorite(
        user_id=user_id,
        facility_id=facility_id,
        favorite_list_id=favorite_list_id,
    )

    db.add(favorite)
    db.commit()
    db.refresh(favorite)

    return favorite


def delete_favorite(
    db: Session,
    favorite: Favorite,
) -> None:
    db.delete(favorite)
    db.commit()