"""
Facilities 라우터 (담당: 이가희) - 총 5개 엔드포인트.
TourAPI는 배치로 미리 적재된 내부 DB(facilities 테이블)를 조회하는 구조 (실시간 프록시 아님).
detailWithTour2 호출은 상세 조회 시 온디맨드로만 연동 (memory 기준).
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import facility as facility_crud
from app.core.database import get_db
from app.schemas.facility import (
    FacilityMatchResult,
    FacilityRead,
    FacilitySummary,
    MatchByLocationRequest,
    MatchByLocationResponse,
)

router = APIRouter(prefix="/facilities", tags=["facilities"])


@router.get("", response_model=list[FacilitySummary])
def list_facilities(category: str | None = None, db: Session = Depends(get_db)):
    """카테고리별 시설 목록."""
    return facility_crud.list_facilities(db, category=category)


# 정적 경로("/search")가 동적 경로("/{facility_id}")보다 먼저 매치되도록 위에 둔다.
# (반대 순서면 "/facilities/search"가 facility_id="search"로 파싱 시도되어 422가 난다)
@router.get("/search", response_model=list[FacilitySummary])
def search_facilities(keyword: str, db: Session = Depends(get_db)):
    """이름/주소 키워드 검색."""
    return facility_crud.search_facilities(db, keyword)


@router.post("/match-by-location", response_model=MatchByLocationResponse)
def match_facility_by_location(payload: MatchByLocationRequest, db: Session = Depends(get_db)):
    """주어진 좌표 반경(m) 내에서 가장 가까운 시설 1건을 매칭 (없으면 matched=false)."""
    candidates = facility_crud.facilities_within_radius(
        db, lat=payload.lat, lng=payload.lng, radius_m=payload.radius
    )
    if not candidates:
        return MatchByLocationResponse(matched=False, message="등록된 무장애 관광 정보가 없습니다.")
    return MatchByLocationResponse(matched=True, facility=FacilityMatchResult.from_facility(candidates[0]))


@router.get("/{facility_id}", response_model=FacilityRead)
def get_facility_detail(facility_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    시설 상세. 프론트에서 locationBasedList2 결과는 메모리에 들고 있다가
    상세 탭 진입 시에만 이 엔드포인트(및 필요 시 detailWithTour2 연동) 호출.
    """
    facility = facility_crud.get_facility(db, facility_id)
    if facility is None:
        raise HTTPException(status_code=404, detail="facility not found")
    return facility


@router.get("/{facility_id}/nearby", response_model=list[FacilitySummary])
def get_nearby_facilities(facility_id: uuid.UUID, radius_m: int = 1000, db: Session = Depends(get_db)):
    """특정 시설 기준 반경 내 주변 시설 (Haversine, 자기 자신 제외)."""
    facility = facility_crud.get_facility(db, facility_id)
    if facility is None:
        raise HTTPException(status_code=404, detail="facility not found")
    return facility_crud.facilities_within_radius(
        db, lat=facility.lat, lng=facility.lng, radius_m=radius_m, exclude_id=facility.id
    )
