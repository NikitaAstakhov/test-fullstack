"""add_index_to_submissions_fname_lname_date

Revision ID: 2801ec7ed18c
Revises: 152942e4ee01
Create Date: 2025-06-01 12:03:13.483821

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2801ec7ed18c'
down_revision: Union[str, None] = '152942e4ee01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_submissions_fname_lname_date",
        "submissions",
        ["first_name", "last_name", "date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_submissions_fname_lname_date", table_name="submissions")
