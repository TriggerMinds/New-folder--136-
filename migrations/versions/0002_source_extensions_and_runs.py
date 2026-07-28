"""source extensions + source_runs

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sources", sa.Column("external_id", sa.String(100), nullable=True))
    op.execute("UPDATE sources SET external_id = 'migrated_' || id::text WHERE external_id IS NULL")
    op.alter_column("sources", "external_id", nullable=False)
    op.create_unique_constraint("uq_sources_external_id", "sources", ["external_id"])
    op.create_index("ix_sources_external_id", "sources", ["external_id"])

    op.add_column("sources", sa.Column("connector_config", postgresql.JSON, nullable=False, server_default="{}"))
    op.add_column("sources", sa.Column("country_pack_version", sa.String(20), nullable=True))

    op.create_table(
        "source_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("success", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("items_seen", sa.Integer, nullable=False, server_default="0"),
        sa.Column("items_matched", sa.Integer, nullable=False, server_default="0"),
        sa.Column("claims_created", sa.Integer, nullable=False, server_default="0"),
        sa.Column("claims_deduplicated", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_source_runs_source_id", "source_runs", ["source_id"])


def downgrade() -> None:
    op.drop_table("source_runs")
    op.drop_column("sources", "country_pack_version")
    op.drop_column("sources", "connector_config")
    op.drop_constraint("uq_sources_external_id", "sources")
    op.drop_index("ix_sources_external_id", "sources")
    op.drop_column("sources", "external_id")
