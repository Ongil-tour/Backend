"""
Map 라우터 (담당: 이가희) - 1개 엔드포인트.
반경 검색 vs 사각형(bounding box) 검색 분기 처리 (memory 기준).

응답은 내부 facilities DB(관광지/식당/카페/숙소 등)와 카카오 로컬 실시간 조회
(편의점/병원)를 UnifiedFacilityItem shape으로 합쳐서 반환한다.
"""
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import facility as facility_crud
from app.core.database import get_db
from app.models.facility import Facility
from app.schemas.facility import UnifiedFacilityItem
from app.services import kakao as kakao_service

router = APIRouter(prefix="/map", tags=["map"])

# 카카오 로컬 category_group_code. 내부 DB에 없는 카테고리만 여기서 다룬다.
KAKAO_CATEGORY_GROUP_CODES = {
    "편의점": "CS2",
    "병원": "HP8",
}
INTERNAL_CATEGORIES = {"관광지", "식당", "카페", "숙소", "화장실", "주차장"}


def _internal_to_unified(facility: Facility) -> UnifiedFacilityItem:
    return UnifiedFacilityItem(
        source="internal",
        id=str(facility.id),
        name=facility.name,
        category=facility.category,
        address=facility.address,
        phone=facility.phone,
        operating_hours=facility.operating_hours,
        lat=facility.lat,
        lng=facility.lng,
        wheelchair_accessible=facility.wheelchair_accessible,
        disabled_restroom=facility.disabled_restroom,
        disabled_parking=facility.disabled_parking,
        elevator=facility.elevator,
        pet_friendly=facility.pet_friendly,
        nursing_room=facility.nursing_room,
    )


def _kakao_doc_to_unified(doc: dict, category: str) -> UnifiedFacilityItem:
    return UnifiedFacilityItem(
        source="kakao",
        id=doc["id"],
        name=doc["place_name"],
        category=category,
        address=doc.get("road_address_name") or doc.get("address_name") or None,
        phone=doc.get("phone") or None,
        operating_hours=None,
        lat=float(doc["y"]),
        lng=float(doc["x"]),
        wheelchair_accessible=None,
        disabled_restroom=None,
        disabled_parking=None,
        elevator=None,
        pet_friendly=None,
        nursing_room=None,
        place_url=doc.get("place_url"),
    )


@router.get("/markers", response_model=list[UnifiedFacilityItem])
def get_map_markers(
    lat: float | None = None,
    lng: float | None = None,
    radius_m: int | None = None,
    sw_lat: float | None = None,
    sw_lng: float | None = None,
    ne_lat: float | None = None,
    ne_lng: float | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
):
    """
    (lat, lng, radius_m) 조합이면 Haversine 반경 검색,
    (sw_*, ne_*) 조합이면 bounding box 검색으로 분기. 로그인 불필요.

    category 미지정 시 내부 DB 카테고리 + 편의점/병원(카카오) 전부 합쳐서 반환.
    카카오 호출이 실패해도 내부 DB 결과는 정상 반환한다 (부분 장애 허용).
    """
    if category is not None and category not in INTERNAL_CATEGORIES and category not in KAKAO_CATEGORY_GROUP_CODES:
        raise HTTPException(status_code=422, detail=f"unknown category: {category}")

    is_radius = lat is not None and lng is not None and radius_m is not None
    is_bounds = None not in (sw_lat, sw_lng, ne_lat, ne_lng)
    if not is_radius and not is_bounds:
        raise HTTPException(
            status_code=422, detail="either (lat, lng, radius_m) or (sw_lat, sw_lng, ne_lat, ne_lng) is required"
        )

    items: list[UnifiedFacilityItem] = []

    if category is None or category in INTERNAL_CATEGORIES:
        internal_category = category if category in INTERNAL_CATEGORIES else None
        if is_radius:
            facilities = facility_crud.facilities_within_radius(
                db, lat=lat, lng=lng, radius_m=radius_m, category=internal_category
            )
        else:
            facilities = facility_crud.facilities_in_bounds(
                db, sw_lat=sw_lat, sw_lng=sw_lng, ne_lat=ne_lat, ne_lng=ne_lng, category=internal_category
            )
        items.extend(_internal_to_unified(f) for f in facilities)

    kakao_targets = (
        KAKAO_CATEGORY_GROUP_CODES.items()
        if category is None
        else [(category, KAKAO_CATEGORY_GROUP_CODES[category])] if category in KAKAO_CATEGORY_GROUP_CODES else []
    )
    for cat_name, group_code in kakao_targets:
        try:
            if is_radius:
                docs = kakao_service.search_by_radius(group_code, lat=lat, lng=lng, radius_m=radius_m)
            else:
                docs = kakao_service.search_by_bounds(
                    group_code, sw_lat=sw_lat, sw_lng=sw_lng, ne_lat=ne_lat, ne_lng=ne_lng
                )
        except httpx.HTTPError:
            continue
        items.extend(_kakao_doc_to_unified(doc, cat_name) for doc in docs)

    return items
