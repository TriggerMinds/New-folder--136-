"""artifact discovery, distribution, reference, acquisition, source_layer

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sources", sa.Column("source_layer", sa.String(20), nullable=False, server_default="reference_only"))
    op.add_column("sources", sa.Column("can_create_artifact_discovery", sa.Boolean, nullable=False, server_default=sa.text("false")))
    op.add_column("sources", sa.Column("can_create_reference_observation", sa.Boolean, nullable=False, server_default=sa.text("true")))

    op.execute("UPDATE sources SET source_layer = 'reference_only' WHERE source_role IN ('confirmation','official_response')")
    op.execute("UPDATE sources SET source_layer = 'primary_raw' WHERE source_role IN ('origin_candidate','distribution','archive','mirror')")
    op.execute("UPDATE sources SET source_layer = 'secondary_discovery' WHERE source_role = 'signal'")
    op.execute("UPDATE sources SET can_create_artifact_discovery = true WHERE source_layer IN ('primary_raw','secondary_discovery')")

    op.create_table(
        "artifact_discoveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("first_observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("parent_claim_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("artifact_type", sa.String(30), nullable=False, server_default="unknown"),
        sa.Column("locator_type", sa.String(30), nullable=False, server_default="unknown"),
        sa.Column("original_locator", sa.Text, nullable=False),
        sa.Column("canonical_locator", sa.Text, nullable=False),
        sa.Column("final_locator", sa.Text, nullable=True),
        sa.Column("host", sa.String(255), nullable=True),
        sa.Column("title", sa.Text, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("filename", sa.String(255), nullable=True),
        sa.Column("file_extension", sa.String(20), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("content_length", sa.Integer, nullable=True),
        sa.Column("sha256", sa.String(64), nullable=True),
        sa.Column("sha1", sa.String(40), nullable=True),
        sa.Column("md5", sa.String(32), nullable=True),
        sa.Column("magnet_uri", sa.Text, nullable=True),
        sa.Column("torrent_infohash", sa.String(40), nullable=True),
        sa.Column("ipfs_cid", sa.String(60), nullable=True),
        sa.Column("repository_url", sa.Text, nullable=True),
        sa.Column("repository_ref", sa.String(100), nullable=True),
        sa.Column("archive_identifier", sa.String(255), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("countries", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("eu_entities", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("national_entities", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("matched_terms", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("raw_metadata", postgresql.JSON, nullable=False, server_default="{}"),
        sa.Column("access_status", sa.String(20), nullable=False, server_default="observed"),
        sa.Column("acquisition_status", sa.String(20), nullable=False, server_default="metadata_only"),
        sa.Column("analysis_status", sa.String(20), nullable=False, server_default="not_started"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_artifact_discoveries_source_id", "artifact_discoveries", ["source_id"])
    op.create_index("ix_artifact_discoveries_canonical_locator", "artifact_discoveries", ["canonical_locator"])
    op.create_index("ix_artifact_discoveries_host", "artifact_discoveries", ["host"])
    op.create_index("ix_artifact_discoveries_sha256", "artifact_discoveries", ["sha256"])
    op.create_index("ix_artifact_discoveries_parent_claim_id", "artifact_discoveries", ["parent_claim_id"])

    op.create_table(
        "distribution_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("artifact_discovery_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("artifact_discoveries.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locator", sa.Text, nullable=False),
        sa.Column("canonical_locator", sa.Text, nullable=False),
        sa.Column("distribution_type", sa.String(30), nullable=False, server_default="unknown"),
        sa.Column("title", sa.Text, nullable=True),
        sa.Column("context_excerpt", sa.Text, nullable=True),
        sa.Column("raw_metadata", postgresql.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_distribution_observations_artifact_id", "distribution_observations", ["artifact_discovery_id"])
    op.create_index("ix_distribution_observations_source_id", "distribution_observations", ["source_id"])

    op.create_table(
        "reference_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("artifact_discovery_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("canonical_url", sa.Text, nullable=False),
        sa.Column("reference_type", sa.String(30), nullable=False, server_default="unknown"),
        sa.Column("title", sa.Text, nullable=True),
        sa.Column("content_excerpt", sa.Text, nullable=True),
        sa.Column("extracted_artifact_locators", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_reference_observations_claim_id", "reference_observations", ["claim_id"])
    op.create_index("ix_reference_observations_artifact_id", "reference_observations", ["artifact_discovery_id"])
    op.create_index("ix_reference_observations_source_id", "reference_observations", ["source_id"])

    op.create_table(
        "artifact_acquisitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("artifact_discovery_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("artifact_discoveries.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(25), nullable=False, server_default="requested"),
        sa.Column("requested_locator", sa.Text, nullable=False),
        sa.Column("final_locator", sa.Text, nullable=True),
        sa.Column("expected_content_length", sa.BigInteger, nullable=True),
        sa.Column("downloaded_bytes", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("calculated_sha256", sa.String(64), nullable=True),
        sa.Column("local_path", sa.Text, nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_artifact_acquisitions_artifact_id", "artifact_acquisitions", ["artifact_discovery_id"])


def downgrade() -> None:
    op.drop_table("artifact_acquisitions")
    op.drop_table("reference_observations")
    op.drop_table("distribution_observations")
    op.drop_table("artifact_discoveries")
    op.drop_column("sources", "can_create_reference_observation")
    op.drop_column("sources", "can_create_artifact_discovery")
    op.drop_column("sources", "source_layer")
