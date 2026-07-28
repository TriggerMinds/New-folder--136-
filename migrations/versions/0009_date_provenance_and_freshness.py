"""date provenance, freshness, source_date_* fields

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("artifact_discoveries", sa.Column("source_created_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("artifact_discoveries", sa.Column("source_modified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("artifact_discoveries", sa.Column("source_date_precision", sa.String(20), nullable=False, server_default="unknown"))
    op.add_column("artifact_discoveries", sa.Column("source_date_confidence", sa.String(20), nullable=False, server_default="unknown"))
    op.add_column("artifact_discoveries", sa.Column("source_date_method", sa.String(30), nullable=False, server_default="unavailable"))
    op.add_column("artifact_discoveries", sa.Column("source_date_raw", sa.String(100), nullable=True))
    op.add_column("artifact_discoveries", sa.Column("freshness_classification", sa.String(30), nullable=False, server_default="unknown"))


def downgrade() -> None:
    for col in ["freshness_classification", "source_date_raw", "source_date_method", "source_date_confidence", "source_date_precision", "source_modified_at", "source_created_at"]:
        op.drop_column("artifact_discoveries", col)
