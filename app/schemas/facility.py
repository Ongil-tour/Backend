import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


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
    ramp: bool | None
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
