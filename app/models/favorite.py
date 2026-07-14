"""
FavoriteList / Favorite 모델.
담당: 신지민. memory 기준 favorite_lists는 list_type만 갖는 3개 고정 리스트로 단순화됨,
favorites는 TourAPI raw 필드 없이 facility_id FK만 참조하도록 정규화됨.

TODO: list_type 3종의 실제 이름(예: WANT_TO_GO/VISITED/CUSTOM 등)은 확정 스키마 문서에서 확인 후 교체.
"""
import enum
from datetime import datetime

from sqlalchemy import ForeignKey, DateTime, Enum, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ListType(str, enum.Enum):
    WANT_TO_GO = "want_to_go"   # TODO: 확정 명칭으로 교체
    VISITED = "visited"          # TODO: 확정 명칭으로 교체
    CUSTOM = "custom"            # TODO: 확정 명칭으로 교체


class FavoriteList(Base):
    __tablename__ = "favorite_lists"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    list_type: Mapped[ListType] = mapped_column(Enum(ListType), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="favorite_lists")
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="favorite_list")

    __table_args__ = (
        UniqueConstraint("user_id", "list_type", name="uq_user_list_type"),
    )


class Favorite(Base):
    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    facility_id: Mapped[int] = mapped_column(ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False)
    favorite_list_id: Mapped[int] = mapped_column(ForeignKey("favorite_lists.id", ondelete="CASCADE"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    favorite_list: Mapped["FavoriteList"] = relationship(back_populates="favorites")

    __table_args__ = (
        UniqueConstraint("favorite_list_id", "facility_id", name="uq_list_facility"),
    )