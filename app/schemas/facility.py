from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FacilityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str | None
    address: str | None
    phone: str | None
    operating_hours: str | None
    latitude: float
    longitude: float

    wheelchair_accessible: bool
    ramp: bool
    disabled_restroom: bool
    disabled_parking: bool
    elevator: bool
    pet_friendly: bool
    nursing_room: bool

    created_at: datetime


class FacilitySummary(BaseModel):
    """지도 마커/리스트용 경량 응답."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str | None
    latitude: float
    longitude: float
    wheelchair_accessible: bool