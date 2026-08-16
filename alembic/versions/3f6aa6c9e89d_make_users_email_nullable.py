"""make users email nullable

Revision ID: 3f6aa6c9e89d
Revises: d3f8a1b9c2e4
Create Date: 2026-08-16 10:24:38.279408

카카오는 최근 정책상 신규 앱의 이메일 제공 권한이 제한돼있어, 이메일 없이도
소셜 로그인 계정 생성이 가능하도록 users.email을 nullable로 변경한다.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f6aa6c9e89d'
down_revision: Union[str, None] = 'd3f8a1b9c2e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'users', 'email',
        existing_type=sa.VARCHAR(length=255),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        'users', 'email',
        existing_type=sa.VARCHAR(length=255),
        nullable=False,
    )
