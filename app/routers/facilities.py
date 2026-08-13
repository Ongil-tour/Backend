"""
Facilities router - 6 endpoints.
TourAPI data is preloaded into the internal facilities table.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import facility as facility_crud
from app.core.database import get_db
from app.schemas.facility import (
    FacilityAccessibility,
    FacilityMatchResult,
    FacilityRead,
    FacilitySummary,
    MatchByLocationRequest,
    MatchByLocationResponse,
)

router = APIRouter(
    prefix="/facilities",
    tags=["facilities"],
)


@router.get("", response_model=list[FacilitySummary])
def list_facilities(
    category: str | None = None,
    db: Session = Depends(get_db),
):
    return facility_crud.list_facilities(
        db,
        category=category,
    )


@router.get("/search", response_model=list[FacilitySummary])
def search_facilities(
    keyword: str,
    db: Session = Depends(get_db),
):
    return facility_crud.search_facilities(
        db,
        keyword,
    )


ALLOWED_RADIUS_KM = (1, 3, 5)


@router.get("/nearby", response_model=list[FacilitySummary])
def get_nearby_facilities(
    lat: float,
    lng: float,
    radius_km: int,
    db: Session = Depends(get_db),
):
    if radius_km not in ALLOWED_RADIUS_KM:
        raise HTTPException(
            status_code=422,
            detail=f"radius_km must be one of {ALLOWED_RADIUS_KM}",
        )

    return facility_crud.facilities_within_radius(
        db,
        lat=lat,
        lng=lng,
        radius_m=radius_km * 1000,
    )


@router.post(
    "/match-by-location",
    response_model=MatchByLocationResponse,
)
def match_facility_by_location(
    payload: MatchByLocationRequest,
    db: Session = Depends(get_db),
):
    candidates = facility_crud.facilities_within_radius(
        db,
        lat=payload.lat,
        lng=payload.lng,
        radius_m=payload.radius,
    )

    if not candidates:
        return MatchByLocationResponse(
            matched=False,
            message="등록된 무장애 관광 정보가 없습니다.",
        )

    return MatchByLocationResponse(
        matched=True,
        facility=FacilityMatchResult.from_facility(
            candidates[0]
        ),
    )


@router.get(
    "/{facility_id}/barrier-free",
    response_model=FacilityAccessibility,
)
def get_facility_barrier_free(
    facility_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    facility = facility_crud.get_facility(
        db,
        facility_id,
    )

    if facility is None:
        raise HTTPException(
            status_code=404,
            detail="facility not found",
        )

    return FacilityAccessibility.from_facility(
        facility
    )


@router.get(
    "/{facility_id}",
    response_model=FacilityRead,
)
def get_facility_detail(
    facility_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    facility = facility_crud.get_facility(
        db,
        facility_id,
    )

    if facility is None:
        raise HTTPException(
            status_code=404,
            detail="facility not found",
        )

    return facility