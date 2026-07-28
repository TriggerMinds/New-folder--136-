"""source lifecycle, present_in_country_pack, disabled_reason, superseded_by

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sources", sa.Column("lifecycle_status", sa.String(20), nullable=False, server_default="active"))
    op.add_column("sources", sa.Column("present_in_country_pack", sa.Boolean, nullable=False, server_default=sa.text("true")))
    op.add_column("sources", sa.Column("disabled_reason", sa.Text, nullable=True))
    op.add_column("sources", sa.Column("superseded_by_source_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("sources", sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_sources_lifecycle_status", "sources", ["lifecycle_status"])
    op.create_index("ix_sources_present_in_country_pack", "sources", ["present_in_country_pack"])

    op.execute("UPDATE sources SET lifecycle_status = CASE WHEN enabled THEN 'active' ELSE 'inactive' END")
    op.execute("UPDATE sources SET present_in_country_pack = true")


def downgrade() -> None:
    op.drop_column("sources", "last_synced_at")
    op.drop_column("sources", "superseded_by_source_id")
    op.drop_column("sources", "disabled_reason")
    op.drop_column("sources", "present_in_country_pack")
    op.drop_column("sources", "lifecycle_status")
