"""record_status, invalidation fields, foreign keys for refs and acquisitions

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("artifact_discoveries", sa.Column("record_status", sa.String(20), nullable=False, server_default="active"))
    op.add_column("artifact_discoveries", sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("artifact_discoveries", sa.Column("invalidation_reason", sa.Text, nullable=True))
    op.create_index("ix_artifact_discoveries_record_status", "artifact_discoveries", ["record_status"])

    op.execute("UPDATE artifact_discoveries SET record_status = 'invalidated', invalidation_reason = 'index or navigation locator incorrectly registered as artifact', invalidated_at = NOW() WHERE access_status = 'invalidated'")
    op.execute("UPDATE artifact_discoveries SET access_status = 'unknown' WHERE access_status = 'invalidated'")

    op.execute("""
        DELETE FROM reference_observations a USING reference_observations b
        WHERE a.id < b.id AND a.artifact_discovery_id = b.artifact_discovery_id
    """)
    op.execute("""
        DELETE FROM artifact_acquisitions a USING artifact_acquisitions b
        WHERE a.id < b.id AND a.artifact_discovery_id = b.artifact_discovery_id
    """)

    op.create_foreign_key("fk_reference_observations_artifact", "reference_observations", "artifact_discoveries", ["artifact_discovery_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_reference_observations_claim", "reference_observations", "observed_leak_claims", ["claim_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_artifact_acquisitions_artifact", "artifact_acquisitions", "artifact_discoveries", ["artifact_discovery_id"], ["id"], ondelete="RESTRICT")
    op.create_index("ix_reference_observations_artifact_discovery_id", "reference_observations", ["artifact_discovery_id"])
    op.create_index("ix_artifact_acquisitions_artifact_discovery_id", "artifact_acquisitions", ["artifact_discovery_id"])

    op.add_column("audit_events", sa.Column("artifact_discovery_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_audit_events_artifact", "audit_events", "artifact_discoveries", ["artifact_discovery_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_audit_events_artifact_discovery_id", "audit_events", ["artifact_discovery_id"])


def downgrade() -> None:
    op.drop_column("audit_events", "artifact_discovery_id")
    op.drop_constraint("fk_artifact_acquisitions_artifact", "artifact_acquisitions")
    op.drop_constraint("fk_reference_observations_claim", "reference_observations")
    op.drop_constraint("fk_reference_observations_artifact", "reference_observations")
    op.drop_index("ix_artifact_acquisitions_artifact_discovery_id", "artifact_acquisitions")
    op.drop_index("ix_reference_observations_artifact_discovery_id", "reference_observations")
    op.drop_column("artifact_discoveries", "invalidation_reason")
    op.drop_column("artifact_discoveries", "invalidated_at")
    op.drop_column("artifact_discoveries", "record_status")
