"""source run metrics and legacy flag

Revision ID: 0012
Revises: 0011
Create Date: 2026-07-28
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("source_runs", sa.Column("raw_items_seen", sa.Integer, nullable=False, server_default="0"))
    op.add_column("source_runs", sa.Column("artifact_candidates_seen", sa.Integer, nullable=False, server_default="0"))
    op.add_column("source_runs", sa.Column("artifacts_created", sa.Integer, nullable=False, server_default="0"))
    op.add_column("source_runs", sa.Column("artifacts_deduplicated", sa.Integer, nullable=False, server_default="0"))
    op.add_column("source_runs", sa.Column("distributions_created", sa.Integer, nullable=False, server_default="0"))
    op.add_column("source_runs", sa.Column("candidates_rejected", sa.Integer, nullable=False, server_default="0"))
    op.add_column("source_runs", sa.Column("artifact_registration_errors", sa.Integer, nullable=False, server_default="0"))
    op.add_column("source_runs", sa.Column("requests_made", sa.Integer, nullable=False, server_default="0"))
    op.add_column("source_runs", sa.Column("rate_limit_remaining", sa.Integer, nullable=True))
    op.add_column("source_runs", sa.Column("legacy_run", sa.Boolean, nullable=False, server_default=sa.text("false")))


def downgrade() -> None:
    for col in ["legacy_run", "rate_limit_remaining", "requests_made", "artifact_registration_errors", "candidates_rejected", "distributions_created", "artifacts_deduplicated", "artifacts_created", "artifact_candidates_seen", "raw_items_seen"]:
        op.drop_column("source_runs", col)
