import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.favorite import ListType


class FavoriteListRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    list_type: ListType
    created_at: datetime


class FavoriteCreate(BaseModel):
    facility_id: uuid.UUID
    list_id: uuid.UUID


class FavoriteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    facility_id: uuid.UUID
    list_id: uuid.UUID
    created_at: datetime


class FavoriteStatusRead(BaseModel):
    is_favorite: bool
    favorite_list_ids: list[uuid.UUID]