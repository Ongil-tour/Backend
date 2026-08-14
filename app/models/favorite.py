import enum
import uuid

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ListType(str, enum.Enum):
    FREQUENT = "FREQUENT"
    WISHLIST = "WISHLIST"
    VISITED = "VISITED"


class FavoriteList(Base):
    __tablename__ = "favorite_lists"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "list_type",
            name="uq_favorite_lists_user_id_list_type",
        ),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    list_type = Column(
        Enum(ListType, name="list_type"),
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    user = relationship(
        "User",
        back_populates="favorite_lists",
    )

    favorites = relationship(
        "Favorite",
        back_populates="favorite_list",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Favorite(Base):
    __tablename__ = "favorites"

    __table_args__ = (
        UniqueConstraint(
            "list_id",
            "facility_id",
            "source",
            name="uq_favorites_list_id_facility_id_source",
        ),
        Index("ix_favorites_facility_id_source", "facility_id", "source"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    list_id = Column(
        UUID(as_uuid=True),
        ForeignKey("favorite_lists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 내부 DB(facilities.id, UUID)와 카카오 로컬 실시간 결과(place id, 숫자 문자열)를
    # 둘 다 담아야 해서 UUID FK가 아니라 문자열로 둔다. 어느 소스인지는 source로 구분한다
    # (app/routers/map.py의 UnifiedFacilityItem.source와 동일한 개념).
    facility_id = Column(
        String(255),
        nullable=False,
    )

    source = Column(
        String(20),
        nullable=False,
        server_default="internal",
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    favorite_list = relationship(
        "FavoriteList",
        back_populates="favorites",
    )
