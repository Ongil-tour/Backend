"""
Facilities 라우터 (담당: 이가희) - 총 4개 엔드포인트.
TourAPI는 배치로 미리 적재된 내부 DB(facilities 테이블)를 조회하는 구조 (실시간 프록시 아님).
detailWithTour2 호출은 상세 조회 시 온디맨드로만 연동 (memory 기준).
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.facility import FacilityRead, FacilitySummary

router = APIRouter(prefix="/facilities", tags=["facilities"])


@router.get("", response_model=list[FacilitySummary])
def list_facilities(category: str | None = None, db: Session = Depends(get_db)):
    """카테고리별 시설 목록. TODO: 구현."""
    raise NotImplementedError


@router.get("/{facility_id}", response_model=FacilityRead)
def get_facility_detail(facility_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    시설 상세. 프론트에서 locationBasedList2 결과는 메모리에 들고 있다가
    상세 탭 진입 시에만 이 엔드포인트(및 필요 시 detailWithTour2 연동) 호출. TODO: 구현.
    """
    raise NotImplementedError


@router.get("/search", response_model=list[FacilitySummary])
def search_facilities(keyword: str, db: Session = Depends(get_db)):
    """키워드 검색. TODO: 구현."""
    raise NotImplementedError


@router.get("/{facility_id}/nearby", response_model=list[FacilitySummary])
def get_nearby_facilities(facility_id: uuid.UUID, radius_m: int = 1000, db: Session = Depends(get_db)):
    """특정 시설 기준 반경 내 주변 시설 (bounding box/Haversine). TODO: 구현."""
    raise NotImplementedError