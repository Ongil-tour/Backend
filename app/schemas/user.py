import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str | None
    created_at: datetime


class UserSettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    high_contrast: bool
    font_size: str
    dark_mode: bool
    profile_image: str
    updated_at: datetime


class UserSettingsUpdate(BaseModel):
    high_contrast: bool | None = None
    font_size: str | None = None
    dark_mode: bool | None = None
    profile_image: str | None = None



class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
