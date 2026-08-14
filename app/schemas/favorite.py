from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.models.favorite import ListType


class FavoriteListCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="생성할 사용자 지정 즐겨찾기 목록 이름",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """
        목록 이름 앞뒤의 공백을 제거한다.

        공백만 입력한 경우에는 목록 이름으로 인정하지 않는다.
        """
        normalized_name = value.strip()

        if not normalized_name:
            raise ValueError(
                "목록 이름은 비어 있을 수 없습니다."
            )

        return normalized_name


class FavoriteListUpdate(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="변경할 사용자 지정 즐겨찾기 목록 이름",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """
        수정할 목록 이름 앞뒤의 공백을 제거한다.
        """
        normalized_name = value.strip()

        if not normalized_name:
            raise ValueError(
                "목록 이름은 비어 있을 수 없습니다."
            )

        return normalized_name


class FavoriteListRead(BaseModel):
    id: UUID
    list_type: ListType
    name: str | None = None
    created_at: datetime
    favorite_count: int = 0

    model_config = ConfigDict(
        from_attributes=True,
    )


class FavoriteCreate(BaseModel):
    facility_id: UUID
    list_id: UUID


class FavoriteRead(BaseModel):
    id: UUID
    facility_id: UUID
    list_id: UUID
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class FavoriteStatusRead(BaseModel):
    is_favorite: bool
    favorite_list_ids: list[UUID]