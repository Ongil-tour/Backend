"""
User / SocialAccount / UserSettings / RefreshToken 모델.
확정 스키마(schema.sql 최종본) 기준. PK는 uuid-ossp의 uuid_generate_v4().
"""
import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Index, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    # cascade와 passive_deletes 옵션 추가
    social_accounts: Mapped[list["SocialAccount"]] = relationship(
        back_populates="user",
        cascade="all, delete",
        passive_deletes=True
    )
    
    settings: Mapped["UserSettings"] = relationship(
        back_populates="user", 
        uselist=False,
        cascade="all, delete",
        passive_deletes=True
    )
    
    favorite_lists: Mapped[list["FavoriteList"]] = relationship(
        back_populates="user",
        cascade="all, delete",
        passive_deletes=True
    )


class SocialAccount(Base):
    """소셜 로그인 연동. 1 user : N social account."""
    __tablename__ = "social_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(20), nullable=False)  # 'google' | 'kakao' | 'naver'
    provider_user_id: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="social_accounts")

    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="social_accounts_provider_provider_user_id_key"),
        Index("idx_social_accounts_user_id", "user_id"),
    )


class UserSettings(Base):
    """사용자 UI 설정. 1 user : 1 setting."""
    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    high_contrast: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    font_size: Mapped[str] = mapped_column(String(10), nullable=False, server_default=text("'md'"))
    dark_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    profile_image: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'profile1.png'"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="settings")

class RefreshToken(Base):
    """Rolling refresh token 저장용 (멀티 디바이스 지원, 1 user : N)."""
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        Index("idx_refresh_tokens_user_id", "user_id"),
    )
