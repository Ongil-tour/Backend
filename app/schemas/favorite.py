from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.favorite import ListType

FacilitySource = Literal["internal", "kakao"]


class FavoriteListRead(BaseModel):
    id: UUID
    list_type: ListType
    created_at: datetime
    favorite_count: int = 0

    model_config = ConfigDict(
        from_attributes=True,
    )


class FavoriteCreate(BaseModel):
    facility_id: str
    source: FacilitySource = "internal"
    list_id: UUID


class FavoriteRead(BaseModel):
    id: UUID
    facility_id: str
    source: FacilitySource
    list_id: UUID
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class FavoriteStatusRead(BaseModel):
    is_favorite: bool
    favorite_list_ids: list[UUID]
