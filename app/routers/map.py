"""
Map 라우터 (담당: 이가희) - 1개 엔드포인트.
반경 검색 vs 사각형(bounding box) 검색 분기 처리 (memory 기준).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import facility as facility_crud
from app.core.database import get_db
from app.schemas.facility import FacilitySummary

router = APIRouter(prefix="/map", tags=["map"])


@router.get("/markers", response_model=list[FacilitySummary])
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
    """
    if lat is not None and lng is not None and radius_m is not None:
        return facility_crud.facilities_within_radius(db, lat=lat, lng=lng, radius_m=radius_m, category=category)
    if None not in (sw_lat, sw_lng, ne_lat, ne_lng):
        return facility_crud.facilities_in_bounds(
            db, sw_lat=sw_lat, sw_lng=sw_lng, ne_lat=ne_lat, ne_lng=ne_lng, category=category
        )
    raise HTTPException(
        status_code=422, detail="either (lat, lng, radius_m) or (sw_lat, sw_lng, ne_lat, ne_lng) is required"
    )