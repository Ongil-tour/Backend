"""
Facility 조회용 쿼리 헬퍼. PostGIS를 쓰지 않으므로 반경 검색은 Haversine 공식을
직접 SQL 함수(acos/cos/sin/radians)로 계산한다 (app/models/facility.py 참고).
"""
import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.facility import Facility


def _distance_expr_m(lat: float, lng: float):
    """주어진 좌표로부터 facilities.lat/lng까지의 거리(m)를 계산하는 SQL 표현식."""
    cos_angle = func.cos(func.radians(lat)) * func.cos(func.radians(Facility.lat)) * func.cos(
        func.radians(Facility.lng) - func.radians(lng)
    ) + func.sin(func.radians(lat)) * func.sin(func.radians(Facility.lat))
    # 부동소수점 오차로 acos 정의역(-1~1)을 벗어나는 것을 방지
    cos_angle_clamped = func.greatest(-1.0, func.least(1.0, cos_angle))
    return 6371000 * func.acos(cos_angle_clamped)


def get_facility(db: Session, facility_id: uuid.UUID) -> Facility | None:
    return db.get(Facility, facility_id)


def list_facilities(db: Session, category: str | None = None) -> list[Facility]:
    query = db.query(Facility)
    if category:
        query = query.filter(Facility.category == category)
    return query.order_by(Facility.name).all()


def search_facilities(db: Session, keyword: str) -> list[Facility]:
    pattern = f"%{keyword}%"
    return (
        db.query(Facility)
        .filter(Facility.name.ilike(pattern) | Facility.address.ilike(pattern))
        .order_by(Facility.name)
        .all()
    )


def facilities_within_radius(
    db: Session,
    lat: float,
    lng: float,
    radius_m: float,
    category: str | None = None,
    exclude_id: uuid.UUID | None = None,
) -> list[Facility]:
    distance = _distance_expr_m(lat, lng)
    query = db.query(Facility).filter(distance <= radius_m)
    if category:
        query = query.filter(Facility.category == category)
    if exclude_id is not None:
        query = query.filter(Facility.id != exclude_id)
    return query.order_by(distance).all()


def facilities_in_bounds(
    db: Session,
    sw_lat: float,
    sw_lng: float,
    ne_lat: float,
    ne_lng: float,
    category: str | None = None,
) -> list[Facility]:
    query = db.query(Facility).filter(
        Facility.lat.between(sw_lat, ne_lat),
        Facility.lng.between(sw_lng, ne_lng),
    )
    if category:
        query = query.filter(Facility.category == category)
    return query.order_by(Facility.name).all()
