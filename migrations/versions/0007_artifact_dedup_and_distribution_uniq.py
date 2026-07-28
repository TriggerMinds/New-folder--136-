"""artifact dedup indexes, distribution unique constraint

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DELETE FROM distribution_observations a USING distribution_observations b
        WHERE a.id < b.id
        AND a.artifact_discovery_id = b.artifact_discovery_id
        AND a.source_id = b.source_id
        AND a.canonical_locator = b.canonical_locator
        AND a.distribution_type = b.distribution_type
    """)
    op.create_unique_constraint(
        "uq_distribution_observations_unique",
        "distribution_observations",
        ["artifact_discovery_id", "source_id", "canonical_locator", "distribution_type"],
    )
    op.create_index("ix_artifact_discoveries_torrent_infohash", "artifact_discoveries", ["torrent_infohash"])
    op.create_index("ix_artifact_discoveries_ipfs_cid", "artifact_discoveries", ["ipfs_cid"])
    op.create_index("ix_artifact_discoveries_archive_identifier", "artifact_discoveries", ["archive_identifier"])
    op.create_index("ix_artifact_discoveries_filename_host", "artifact_discoveries", ["filename", "host"])


def downgrade() -> None:
    op.drop_constraint("uq_distribution_observations_unique", "distribution_observations")
    op.drop_index("ix_artifact_discoveries_torrent_infohash", "artifact_discoveries")
    op.drop_index("ix_artifact_discoveries_ipfs_cid", "artifact_discoveries")
    op.drop_index("ix_artifact_discoveries_archive_identifier", "artifact_discoveries")
    op.drop_index("ix_artifact_discoveries_filename_host", "artifact_discoveries")
