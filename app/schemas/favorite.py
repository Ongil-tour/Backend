from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.favorite import ListType


class FavoriteListRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    list_type: ListType
    created_at: datetime


class FavoriteCreate(BaseModel):
    facility_id: int
    favorite_list_id: int


class FavoriteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    facility_id: int
    favorite_list_id: int
    created_at: datetime