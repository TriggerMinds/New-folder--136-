"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    for type_sql in [
        """
        DO $$ BEGIN
            CREATE TYPE authenticity_status AS ENUM (
                'unexamined', 'verified_authentic', 'likely_authentic',
                'likely_fabricated', 'confirmed_fabricated', 'disputed', 'unverifiable'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """,
        """
        DO $$ BEGIN
            CREATE TYPE provenance_status AS ENUM (
                'unknown', 'traced', 'partially_traced', 'attributed',
                'confirmed_anonymous', 'confirmed_whistleblower', 'confirmed_state_actor'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """,
        """
        DO $$ BEGIN
            CREATE TYPE content_access_status AS ENUM (
                'public', 'paywalled', 'restricted', 'deleted', 'unavailable'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """,
        """
        DO $$ BEGIN
            CREATE TYPE ai_enrichment_status AS ENUM (
                'pending', 'enriched', 'failed', 'skipped'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """,
    ]:
        op.execute(type_sql)

    op.create_table(
        "observed_leak_claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("record_type", sa.String(50), nullable=False, server_default="observed_leak_claim"),
        sa.Column("first_observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("title_original", sa.Text, nullable=False),
        sa.Column("title_translated", sa.Text, nullable=True),
        sa.Column("source_language", sa.String(10), nullable=True),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("claim_text", sa.Text, nullable=True),
        sa.Column("countries", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("eu_entities", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("national_entities", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("dossiers", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("first_observed_url", sa.Text, nullable=False),
        sa.Column("first_observed_host", sa.String(255), nullable=False),
        sa.Column("earliest_known_public_url", sa.Text, nullable=True),
        sa.Column("earliest_known_public_host", sa.String(255), nullable=True),
        sa.Column("claimed_origin_url", sa.Text, nullable=True),
        sa.Column("claimed_origin_host", sa.String(255), nullable=True),
        sa.Column("confirmed_origin_url", sa.Text, nullable=True),
        sa.Column("confirmed_origin_host", sa.String(255), nullable=True),
        sa.Column("authenticity_status", postgresql.ENUM("unexamined", "verified_authentic", "likely_authentic", "likely_fabricated", "confirmed_fabricated", "disputed", "unverifiable", name="authenticity_status", create_type=False), nullable=False, server_default="unexamined"),
        sa.Column("provenance_status", postgresql.ENUM("unknown", "traced", "partially_traced", "attributed", "confirmed_anonymous", "confirmed_whistleblower", "confirmed_state_actor", name="provenance_status", create_type=False), nullable=False, server_default="unknown"),
        sa.Column("content_access_status", postgresql.ENUM("public", "paywalled", "restricted", "deleted", "unavailable", name="content_access_status", create_type=False), nullable=False, server_default="public"),
        sa.Column("ai_enrichment_status", postgresql.ENUM("pending", "enriched", "failed", "skipped", name="ai_enrichment_status", create_type=False), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_observed_leak_claims_first_observed_at", "observed_leak_claims", ["first_observed_at"])
    op.create_index("ix_observed_leak_claims_first_observed_host", "observed_leak_claims", ["first_observed_host"])

    op.create_table(
        "sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=False),
        sa.Column("languages", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("base_url", sa.Text, nullable=False),
        sa.Column("poll_url", sa.Text, nullable=False),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("poll_interval_minutes", sa.Integer, nullable=False, server_default="30"),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text, nullable=True),
        sa.Column("consecutive_failures", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_sources_country_code", "sources", ["country_code"])
    op.create_index("ix_sources_enabled", "sources", ["enabled"])

    op.create_table(
        "observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("observed_leak_claims.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("canonical_url", sa.Text, nullable=False),
        sa.Column("host", sa.String(255), nullable=False),
        sa.Column("http_status", sa.Integer, nullable=True),
        sa.Column("title", sa.Text, nullable=True),
        sa.Column("content_excerpt", sa.Text, nullable=True),
        sa.Column("content_hash_sha256", sa.String(64), nullable=True),
        sa.Column("discovery_method", sa.String(50), nullable=False),
        sa.Column("connector_type", sa.String(50), nullable=False),
        sa.Column("connector_version", sa.String(20), nullable=False),
        sa.Column("raw_metadata", postgresql.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_observations_canonical_url", "observations", ["canonical_url"])
    op.create_index("ix_observations_content_hash_sha256", "observations", ["content_hash_sha256"])
    op.create_index("ix_observations_claim_id", "observations", ["claim_id"])
    op.create_index("ix_observations_source_id", "observations", ["source_id"])

    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("observed_leak_claims.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("actor", sa.String(100), nullable=False),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("field_name", sa.String(100), nullable=True),
        sa.Column("old_value", postgresql.JSON, nullable=True),
        sa.Column("new_value", postgresql.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_events_claim_id", "audit_events", ["claim_id"])


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("observations")
    op.drop_table("sources")
    op.drop_table("observed_leak_claims")
    op.execute("DROP TYPE IF EXISTS ai_enrichment_status")
    op.execute("DROP TYPE IF EXISTS content_access_status")
    op.execute("DROP TYPE IF EXISTS provenance_status")
    op.execute("DROP TYPE IF EXISTS authenticity_status")
