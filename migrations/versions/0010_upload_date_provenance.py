"""upload date provenance: source_uploaded_at, upload_date_method/confidence/raw

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-28
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("artifact_discoveries", sa.Column("source_uploaded_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("artifact_discoveries", sa.Column("upload_date_method", sa.String(30), nullable=False, server_default="unavailable"))
    op.add_column("artifact_discoveries", sa.Column("upload_date_confidence", sa.String(20), nullable=False, server_default="unknown"))
    op.add_column("artifact_discoveries", sa.Column("upload_date_raw", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("artifact_discoveries", "upload_date_raw")
    op.drop_column("artifact_discoveries", "upload_date_confidence")
    op.drop_column("artifact_discoveries", "upload_date_method")
    op.drop_column("artifact_discoveries", "source_uploaded_at")
