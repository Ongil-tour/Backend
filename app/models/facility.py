"""
Facility(시설) 마스터 테이블.
담당: 이가희. 접근성 필드 7종 확정됨 (memory 기준) - 실제 컬럼명은 schema.sql/DBML과 대조 필요.
좌표는 double(lat/lng)로 응답용 유지 + geom(PostGIS Point)으로 공간쿼리(ST_DWithin)용 이중 관리.
"""
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import String, Float, Boolean, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Facility(Base):
    __tablename__ = "facilities"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # TourAPI 원본 콘텐츠 id (batch 적재 시 중복 방지용 unique key)
    tour_api_content_id: Mapped[str | None] = mapped_column(String(50), unique=True, index=True, nullable=True)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 관광지/식당/카페/숙소/화장실/주차장 등
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    operating_hours: Mapped[str | None] = mapped_column(String(300), nullable=True)

    # 응답용 좌표 (double)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    # 공간 쿼리용 (ST_DWithin 등). SRID 4326 = WGS84
    # spatial_index=False: GIST 인덱스는 아래 __table_args__의 ix_facilities_geom으로 명시 관리 (중복 방지)
    geom: Mapped[str] = mapped_column(Geometry(geometry_type="POINT", srid=4326, spatial_index=False), nullable=False)

    # 접근성 필드 7종 (memory 기준 확정)
    wheelchair_accessible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ramp: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    disabled_restroom: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    disabled_parking: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    elevator: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    pet_friendly: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    nursing_room: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_facilities_geom", "geom", postgresql_using="gist"),
    )