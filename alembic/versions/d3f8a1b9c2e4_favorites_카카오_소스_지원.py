"""favorites 카카오 소스 지원 (facility_id UUID FK -> 문자열 + source)

Revision ID: d3f8a1b9c2e4
Revises: eb1303a93644
Create Date: 2026-08-14 00:00:00.000000

즐겨찾기가 내부 DB(facilities.id, UUID)뿐 아니라 카카오 로컬 실시간 결과(숫자 문자열 place id)도
저장할 수 있도록 facility_id를 UUID FK에서 문자열로 바꾸고 source 컬럼을 추가한다.
카카오 소스는 저장 시점에 존재 검증을 하지 않는다 (재조회는 쿼터 낭비라 프론트 입력을 신뢰).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3f8a1b9c2e4'
down_revision: Union[str, None] = 'eb1303a93644'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('favorites_facility_id_fkey', 'favorites', type_='foreignkey')
    op.drop_constraint('favorites_list_id_facility_id_key', 'favorites', type_='unique')
    op.drop_index('idx_favorites_facility_id', table_name='favorites')

    op.alter_column(
        'favorites',
        'facility_id',
        type_=sa.String(255),
        existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
        postgresql_using='facility_id::text',
    )
    op.add_column(
        'favorites',
        sa.Column('source', sa.String(20), nullable=False, server_default='internal'),
    )

    op.create_unique_constraint(
        'uq_favorites_list_id_facility_id_source', 'favorites', ['list_id', 'facility_id', 'source']
    )
    op.create_index('ix_favorites_facility_id_source', 'favorites', ['facility_id', 'source'])


def downgrade() -> None:
    op.drop_index('ix_favorites_facility_id_source', table_name='favorites')
    op.drop_constraint('uq_favorites_list_id_facility_id_source', 'favorites', type_='unique')

    op.drop_column('favorites', 'source')
    op.alter_column(
        'favorites',
        'facility_id',
        type_=sa.dialects.postgresql.UUID(as_uuid=True),
        existing_type=sa.String(255),
        postgresql_using='facility_id::uuid',
    )

    op.create_index('idx_favorites_facility_id', 'favorites', ['facility_id'])
    op.create_unique_constraint(
        'favorites_list_id_facility_id_key', 'favorites', ['list_id', 'facility_id']
    )
    op.create_foreign_key(
        'favorites_facility_id_fkey', 'favorites', 'facilities', ['facility_id'], ['id'], ondelete='CASCADE'
    )
