"""
FavoriteList / Favorite 모델. 확정 스키마(schema.sql 최종본) 기준.
favorite_lists는 회원가입 시 FREQUENT/WISHLIST/VISITED 3종이 자동 생성되는 고정 리스트.
list_type은 DB에는 plain varchar로 저장하고, 라벨(자주가는곳/가고싶은곳/다녀온곳)은
DB에 저장하지 않고 앱 코드에서 매핑한다.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, DateTime, String, Index, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ListType(str, enum.Enum):
    FREQUENT = "FREQUENT"
    WISHLIST = "WISHLIST"
    VISITED = "VISITED"


class FavoriteList(Base):
    __tablename__ = "favorite_lists"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    list_type: Mapped[str] = mapped_column(String(20), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="favorite_lists")
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="favorite_list")

    __table_args__ = (
        UniqueConstraint("user_id", "list_type", name="favorite_lists_user_id_list_type_key"),
        Index("idx_favorite_lists_user_id", "user_id"),
    )


class Favorite(Base):
    """즐겨찾기 항목 (리스트 - 시설 매핑)."""
    __tablename__ = "favorites"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    list_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("favorite_lists.id", ondelete="CASCADE"), nullable=False
    )
    # 내부 DB(facilities.id, UUID)와 카카오 로컬 실시간 결과(place id, 숫자 문자열)를
    # 둘 다 담아야 해서 UUID FK가 아니라 문자열로 둔다. 어느 소스인지는 source로 구분한다
    # (app/routers/map.py의 UnifiedFacilityItem.source와 동일한 개념).
    facility_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'internal'"))

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    favorite_list: Mapped["FavoriteList"] = relationship(back_populates="favorites")

    __table_args__ = (
        UniqueConstraint(
            "list_id", "facility_id", "source", name="favorites_list_id_facility_id_source_key"
        ),
        Index("idx_favorites_user_id", "user_id"),
        Index("idx_favorites_list_id", "list_id"),
        Index("idx_favorites_facility_id_source", "facility_id", "source"),
    )
