"""source roles, categories, source_signal

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sources", sa.Column("source_role", sa.String(30), nullable=False, server_default="signal"))
    op.add_column("sources", sa.Column("source_category", sa.String(30), nullable=False, server_default="specialist_blog"))
    op.add_column("sources", sa.Column("can_create_primary_claim", sa.Boolean, nullable=False, server_default=sa.text("true")))
    op.add_column("sources", sa.Column("discovery_priority", sa.String(10), nullable=False, server_default="secondary"))

    op.create_table(
        "source_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("title", sa.Text, nullable=True),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("canonical_url", sa.Text, nullable=False),
        sa.Column("content_excerpt", sa.Text, nullable=True),
        sa.Column("source_role", sa.String(30), nullable=False),
        sa.Column("source_category", sa.String(30), nullable=False),
        sa.Column("matched_terms", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("extracted_urls", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("extracted_hashes", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("extracted_magnet_links", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("extracted_ipfs_cids", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("extracted_file_names", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("processing_status", sa.String(30), nullable=False, server_default="pending_origin_resolution"),
        sa.Column("linked_claim_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_source_signals_source_id", "source_signals", ["source_id"])
    op.create_index("ix_source_signals_linked_claim_id", "source_signals", ["linked_claim_id"])


def downgrade() -> None:
    op.drop_table("source_signals")
    op.drop_column("sources", "discovery_priority")
    op.drop_column("sources", "can_create_primary_claim")
    op.drop_column("sources", "source_category")
    op.drop_column("sources", "source_role")
