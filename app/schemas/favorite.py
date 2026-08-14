import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.models.favorite import ListType

FacilitySource = Literal["internal", "kakao"]


class FavoriteListRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    list_type: ListType
    favorite_count: int
    created_at: datetime


class FavoriteCreate(BaseModel):
    facility_id: str
    source: FacilitySource = "internal"
    list_id: uuid.UUID


class FavoriteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    facility_id: str
    source: FacilitySource
    list_id: uuid.UUID
    created_at: datetime


class FavoriteStatusRead(BaseModel):
    is_favorite: bool
    favorite_list_ids: list[uuid.UUID]