"""sync favorite list type enum

Revision ID: eb1303a93644
Revises: cc0aff69eb9c
Create Date: 2026-07-31 09:43:47.106184

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "eb1303a93644"
down_revision: Union[str, None] = "cc0aff69eb9c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


list_type_enum = postgresql.ENUM(
    "FREQUENT",
    "WISHLIST",
    "VISITED",
    name="list_type",
)


def upgrade() -> None:
    list_type_enum.create(
        op.get_bind(),
        checkfirst=True,
    )

    op.alter_column(
        "favorite_lists",
        "list_type",
        existing_type=sa.String(length=20),
        type_=list_type_enum,
        existing_nullable=False,
        postgresql_using="list_type::text::list_type",
    )


def downgrade() -> None:
    op.alter_column(
        "favorite_lists",
        "list_type",
        existing_type=list_type_enum,
        type_=sa.String(length=20),
        existing_nullable=False,
        postgresql_using="list_type::text",
    )

    list_type_enum.drop(
        op.get_bind(),
        checkfirst=True,
    )