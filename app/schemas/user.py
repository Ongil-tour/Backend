import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
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
    # 허용값을 Literal로 타입에 박아두면 Pydantic이 알아서 422를 내줘서
    # app/crud/user.py 쪽 수동 검증(HTTPException)이 필요 없어짐.
    font_size: Literal["sm", "md", "lg"] | None = None
    dark_mode: bool | None = None
    profile_image: Literal["profile1.png", "profile2.png", "profile3.png", "profile4.png"] | None = None



class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
