"""add custom favorite lists

Revision ID: eb1303a93644
Revises: cc0aff69eb9c
Create Date: 2026-07-31 09:43:47.106184

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'eb1303a93644'
down_revision: Union[str, None] = 'cc0aff69eb9c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
def upgrade() -> None:
    op.add_column(
        "favorite_lists",
        sa.Column(
            "name",
            sa.String(length=50),
            nullable=True,
        ),
    )

    op.drop_constraint(
        "favorite_lists_user_id_list_type_key",
        "favorite_lists",
        type_="unique",
    )

    op.create_unique_constraint(
        "uq_favorite_lists_user_id_name",
        "favorite_lists",
        ["user_id", "name"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_favorite_lists_user_id_name",
        "favorite_lists",
        type_="unique",
    )

    op.create_unique_constraint(
        "favorite_lists_user_id_list_type_key",
        "favorite_lists",
        ["user_id", "list_type"],
    )

    op.drop_column(
        "favorite_lists",
        "name",
    )