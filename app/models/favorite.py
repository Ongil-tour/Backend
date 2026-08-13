import enum
import uuid

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
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
            name="uq_favorites_list_id_facility_id",
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

    facility_id = Column(
        UUID(as_uuid=True),
        ForeignKey("facilities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    list_id = Column(
        UUID(as_uuid=True),
        ForeignKey("favorite_lists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
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

    facility = relationship("Facility")