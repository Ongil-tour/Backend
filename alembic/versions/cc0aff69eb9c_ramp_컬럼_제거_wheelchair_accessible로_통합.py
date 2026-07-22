"""ramp 컬럼 제거, wheelchair_accessible로 통합

Revision ID: cc0aff69eb9c
Revises: a804741c7b4c
Create Date: 2026-07-19 00:00:00.000000

ramp(경사로)와 wheelchair_accessible(휠체어 접근 가능)이 의미상 겹쳐(휠체어 경사로)
무장애 정보를 wheelchair_accessible 하나로 통합한다 (app/services/facility_sync.py 참고).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc0aff69eb9c'
down_revision: Union[str, None] = 'a804741c7b4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('facilities', 'ramp')


def downgrade() -> None:
    op.add_column(
        'facilities',
        sa.Column('ramp', sa.Boolean(), server_default=sa.text('false'), nullable=True),
    )
