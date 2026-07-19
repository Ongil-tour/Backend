"""init schema

Revision ID: a4960384307e
Revises:
Create Date: 2026-07-15

확정 스키마(schema.sql 최종본)를 그대로 반영. SQLAlchemy 모델을 통한 변환 없이
raw SQL로 실행해 DDL이 확정 문서와 100% 일치하도록 한다.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a4960384307e"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    op.execute("""
        CREATE TABLE users (
            id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            email       VARCHAR(255) NOT NULL UNIQUE,
            created_at  TIMESTAMP NOT NULL DEFAULT now()
        );
    """)

    op.execute("""
        CREATE TABLE social_accounts (
            id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            provider          VARCHAR(20) NOT NULL,
            provider_user_id  VARCHAR(100) NOT NULL,
            created_at        TIMESTAMP NOT NULL DEFAULT now(),
            UNIQUE (provider, provider_user_id)
        );
    """)
    op.execute("CREATE INDEX idx_social_accounts_user_id ON social_accounts(user_id);")

    op.execute("""
        CREATE TABLE user_settings (
            user_id       UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            high_contrast BOOLEAN NOT NULL DEFAULT false,
            font_size     VARCHAR(10) NOT NULL DEFAULT 'md',
            updated_at    TIMESTAMP NOT NULL DEFAULT now()
        );
    """)

    op.execute("""
        CREATE TABLE refresh_tokens (
            id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token       VARCHAR(512) NOT NULL UNIQUE,
            expires_at  TIMESTAMP NOT NULL,
            created_at  TIMESTAMP NOT NULL DEFAULT now()
        );
    """)
    op.execute("CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);")

    op.execute("""
        CREATE TABLE facilities (
            id                     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

            content_id             VARCHAR(20) NOT NULL UNIQUE,
            content_type_id        VARCHAR(10) NOT NULL,

            name                   VARCHAR(100) NOT NULL,
            category               VARCHAR(20),
            address                VARCHAR(255),
            lat                    DOUBLE PRECISION NOT NULL,
            lng                    DOUBLE PRECISION NOT NULL,
            operating_hours        VARCHAR(100),
            phone                  VARCHAR(30),

            wheelchair_accessible  BOOLEAN DEFAULT false,
            ramp                   BOOLEAN DEFAULT false,
            disabled_restroom      BOOLEAN DEFAULT false,
            disabled_parking       BOOLEAN DEFAULT false,
            elevator               BOOLEAN DEFAULT false,
            pet_friendly           BOOLEAN DEFAULT false,
            nursing_room           BOOLEAN DEFAULT false,

            synced_at              TIMESTAMP NOT NULL DEFAULT now(),
            created_at             TIMESTAMP NOT NULL DEFAULT now()
        );
    """)
    op.execute("CREATE INDEX idx_facilities_lat_lng ON facilities(lat, lng);")
    op.execute("CREATE INDEX idx_facilities_category ON facilities(category);")

    op.execute("""
        CREATE TABLE favorite_lists (
            id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            list_type   VARCHAR(20) NOT NULL,
            created_at  TIMESTAMP NOT NULL DEFAULT now(),
            UNIQUE (user_id, list_type)
        );
    """)
    op.execute("CREATE INDEX idx_favorite_lists_user_id ON favorite_lists(user_id);")

    op.execute("""
        CREATE TABLE favorites (
            id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            list_id      UUID NOT NULL REFERENCES favorite_lists(id) ON DELETE CASCADE,
            facility_id  UUID NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
            created_at   TIMESTAMP NOT NULL DEFAULT now(),
            UNIQUE (list_id, facility_id)
        );
    """)
    op.execute("CREATE INDEX idx_favorites_user_id ON favorites(user_id);")
    op.execute("CREATE INDEX idx_favorites_list_id ON favorites(list_id);")
    op.execute("CREATE INDEX idx_favorites_facility_id ON favorites(facility_id);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS favorites;")
    op.execute("DROP TABLE IF EXISTS favorite_lists;")
    op.execute("DROP TABLE IF EXISTS facilities;")
    op.execute("DROP TABLE IF EXISTS refresh_tokens;")
    op.execute("DROP TABLE IF EXISTS user_settings;")
    op.execute("DROP TABLE IF EXISTS social_accounts;")
    op.execute("DROP TABLE IF EXISTS users;")
