import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FacilityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    content_id: str
    content_type_id: str
    name: str
    category: str | None
    address: str | None
    phone: str | None
    operating_hours: str | None
    lat: float
    lng: float

    wheelchair_accessible: bool | None
    disabled_restroom: bool | None
    disabled_parking: bool | None
    elevator: bool | None
    pet_friendly: bool | None
    nursing_room: bool | None

    synced_at: datetime
    created_at: datetime


class FacilitySummary(BaseModel):
    """지도 마커/리스트용 경량 응답."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    category: str | None
    lat: float
    lng: float
    wheelchair_accessible: bool | None


class MatchByLocationRequest(BaseModel):
    lat: float
    lng: float
    radius: float = 100


class FacilityAccessibility(BaseModel):
    """무장애 정보 6종. camelCase 응답 계약을 위해 alias를 둔다."""
    model_config = ConfigDict(populate_by_name=True)

    wheelchair_accessible: bool = Field(alias="wheelchairAccessible")
    disabled_restroom: bool = Field(alias="disabledRestroom")
    parking_lot: bool = Field(alias="parkingLot")
    elevator: bool
    pet_friendly: bool = Field(alias="petFriendly")
    nursing_room: bool = Field(alias="nursingRoom")

    @classmethod
    def from_facility(cls, facility) -> "FacilityAccessibility":
        return cls(
            wheelchair_accessible=bool(facility.wheelchair_accessible),
            disabled_restroom=bool(facility.disabled_restroom),
            parking_lot=bool(facility.disabled_parking),
            elevator=bool(facility.elevator),
            pet_friendly=bool(facility.pet_friendly),
            nursing_room=bool(facility.nursing_room),
        )


class FacilityMatchResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    name: str
    address: str | None
    lat: float
    lng: float
    operating_hours: str | None = Field(alias="operatingHours")
    phone: str | None
    accessibility: FacilityAccessibility

    @classmethod
    def from_facility(cls, facility) -> "FacilityMatchResult":
        return cls(
            id=facility.id,
            name=facility.name,
            address=facility.address,
            lat=facility.lat,
            lng=facility.lng,
            operating_hours=facility.operating_hours,
            phone=facility.phone,
            accessibility=FacilityAccessibility.from_facility(facility),
        )


class MatchByLocationResponse(BaseModel):
    matched: bool
    facility: FacilityMatchResult | None = None
    message: str | None = None


class UnifiedFacilityItem(BaseModel):
    """/map/markers 통합 응답. 내부 facilities DB + 카카오 로컬(편의점/병원 실시간)을
    같은 shape으로 합친다. kakao 소스는 무장애 6종/operating_hours가 전부 None
    (실제 값이 아니라 '정보 없음'이라는 뜻 - 카카오 로컬 API가 해당 정보를 제공하지 않음)."""

    source: Literal["internal", "kakao"]
    id: str  # internal=uuid 문자열, kakao=place id 문자열
    name: str
    category: str  # 관광지|식당|카페|숙소|화장실|주차장|편의점|병원
    address: str | None
    phone: str | None
    operating_hours: str | None
    lat: float
    lng: float

    wheelchair_accessible: bool | None
    disabled_restroom: bool | None
    disabled_parking: bool | None
    elevator: bool | None
    pet_friendly: bool | None
    nursing_room: bool | None

    place_url: str | None = None  # kakao 상세 링크. internal은 None
