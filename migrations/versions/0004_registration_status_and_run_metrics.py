"""registration_status, run metrics, item errors

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("observed_leak_claims", sa.Column("registration_status", sa.String(20), nullable=False, server_default="active"))
    op.create_index("ix_observed_leak_claims_registration_status", "observed_leak_claims", ["registration_status"])

    op.add_column("source_runs", sa.Column("run_status", sa.String(20), nullable=False, server_default="success"))
    op.add_column("source_runs", sa.Column("item_errors_count", sa.Integer, nullable=False, server_default="0"))
    op.add_column("source_runs", sa.Column("item_errors", postgresql.JSON, nullable=False, server_default="[]"))
    op.add_column("source_runs", sa.Column("artifact_items_seen", sa.Integer, nullable=False, server_default="0"))
    op.add_column("source_runs", sa.Column("eu_entity_matches", sa.Integer, nullable=False, server_default="0"))
    op.add_column("source_runs", sa.Column("leak_assertion_matches", sa.Integer, nullable=False, server_default="0"))
    op.add_column("source_runs", sa.Column("context_only_matches", sa.Integer, nullable=False, server_default="0"))
    op.add_column("source_runs", sa.Column("primary_claim_candidates", sa.Integer, nullable=False, server_default="0"))
    op.add_column("source_runs", sa.Column("source_signals_created", sa.Integer, nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("source_runs", "source_signals_created")
    op.drop_column("source_runs", "primary_claim_candidates")
    op.drop_column("source_runs", "context_only_matches")
    op.drop_column("source_runs", "leak_assertion_matches")
    op.drop_column("source_runs", "eu_entity_matches")
    op.drop_column("source_runs", "artifact_items_seen")
    op.drop_column("source_runs", "item_errors")
    op.drop_column("source_runs", "item_errors_count")
    op.drop_column("source_runs", "run_status")
    op.drop_index("ix_observed_leak_claims_registration_status", "observed_leak_claims")
    op.drop_column("observed_leak_claims", "registration_status")
