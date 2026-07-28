"""repository_pushed_at, source_added_at, freshness fields

Revision ID: 0011
Revises: 0010
Create Date: 2026-07-28
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("artifact_discoveries", sa.Column("repository_pushed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("artifact_discoveries", sa.Column("source_added_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("artifact_discoveries", sa.Column("source_date_evidence", sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column("artifact_discoveries", "source_date_evidence")
    op.drop_column("artifact_discoveries", "source_added_at")
    op.drop_column("artifact_discoveries", "repository_pushed_at")
