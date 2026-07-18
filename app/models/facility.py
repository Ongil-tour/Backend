"""
Facility(시설) 마스터 테이블. 확정 스키마(schema.sql 최종본) 기준.
좌표는 lat/lng(double)만 사용한다 - PostGIS는 쓰지 않으며, 반경/영역 검색은
bounding box 또는 Haversine 공식으로 처리한다 (라우터 구현 시 참고).
"""
import uuid
from datetime import datetime

from sqlalchemy import String, Float, Boolean, DateTime, Index, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Facility(Base):
    __tablename__ = "facilities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )

    # 관광공사 TourAPI 원본 식별자
    content_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # TourAPI contentId
    content_type_id: Mapped[str] = mapped_column(String(10), nullable=False)  # 12:관광지 32:숙소 39:음식점 등

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 관광지|식당|카페|숙소|화장실|주차장
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    operating_hours: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # 한국관광공사 무장애 정보 (6종 확정)
    wheelchair_accessible: Mapped[bool | None] = mapped_column(Boolean, server_default=text("false"))
    ramp: Mapped[bool | None] = mapped_column(Boolean, server_default=text("false"))
    disabled_restroom: Mapped[bool | None] = mapped_column(Boolean, server_default=text("false"))
    disabled_parking: Mapped[bool | None] = mapped_column(Boolean, server_default=text("false"))
    elevator: Mapped[bool | None] = mapped_column(Boolean, server_default=text("false"))
    pet_friendly: Mapped[bool | None] = mapped_column(Boolean, server_default=text("false"))
    nursing_room: Mapped[bool | None] = mapped_column(Boolean, server_default=text("false"))

    synced_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())  # 배치 최종 갱신 시각
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        Index("idx_facilities_lat_lng", "lat", "lng"),
        Index("idx_facilities_category", "category"),
    )
