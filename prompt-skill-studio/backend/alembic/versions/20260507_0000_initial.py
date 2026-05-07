"""initial schema

Revision ID: 20260507_0000
Revises:
Create Date: 2026-05-07
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260507_0000"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    vendor = sa.Enum("anthropic", "openai", name="vendor_enum")
    artifact_type = sa.Enum("prompt", "skill", "agent", "mcp", name="artifact_type_enum")
    run_status = sa.Enum(
        "pending", "streaming", "completed", "failed", name="run_status_enum"
    )
    mcp_transport = sa.Enum("stdio", "http", "sse", name="mcp_transport_enum")
    mcp_language = sa.Enum("typescript", "python", name="mcp_language_enum")
    catalog_kind = sa.Enum(
        "model", "feature", "beta", "technique", "pricing", name="catalog_kind_enum"
    )
    for e in (vendor, artifact_type, run_status, mcp_transport, mcp_language, catalog_kind):
        e.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "app_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("require_login", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("login_passcode_hash", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "vendor_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vendor", vendor, nullable=False),
        sa.Column("label", sa.String(120), nullable=False),
        sa.Column("fingerprint", sa.String(40), nullable=False),
        sa.Column("nonce", sa.LargeBinary(12), nullable=False),
        sa.Column("ciphertext", sa.LargeBinary, nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "prompts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("body", sa.Text, nullable=False, server_default=""),
        sa.Column("variables", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("tags", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("frontmatter", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("body", sa.Text, nullable=False, server_default=""),
        sa.Column("files", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "agents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("vendor", vendor, nullable=False),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("instructions", sa.Text, nullable=False, server_default=""),
        sa.Column("tools", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("mcp_refs", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "mcp_servers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("transport", mcp_transport, nullable=False),
        sa.Column("language", mcp_language, nullable=False),
        sa.Column("tools", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("artifact_type", artifact_type, nullable=False),
        sa.Column("artifact_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("vendor", vendor, nullable=False),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("input", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("output", sa.Text, nullable=False, server_default=""),
        sa.Column("usage", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column("status", run_status, nullable=False, server_default="pending"),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "key_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("vendor_keys.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "vendor_catalog",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vendor", vendor, nullable=False),
        sa.Column("kind", catalog_kind, nullable=False),
        sa.Column("slug", sa.String(200), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("props", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("source_url", sa.String(500), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("vendor", "slug", "content_hash", name="uq_catalog_vsh"),
    )
    op.create_index("ix_vendor_catalog_vendor_kind", "vendor_catalog", ["vendor", "kind"])

    op.create_table(
        "vendor_changelog",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vendor", vendor, nullable=False),
        sa.Column("source_url", sa.String(500), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status_code", sa.Integer, nullable=False),
        sa.Column("raw_blob_path", sa.String(500), nullable=True),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("diff", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_vendor_changelog_fetched_at", "vendor_changelog", ["fetched_at"])


def downgrade() -> None:
    for t in (
        "vendor_changelog",
        "vendor_catalog",
        "runs",
        "mcp_servers",
        "agents",
        "skills",
        "prompts",
        "vendor_keys",
        "app_settings",
    ):
        op.drop_table(t)
    for e in (
        "catalog_kind_enum",
        "mcp_language_enum",
        "mcp_transport_enum",
        "run_status_enum",
        "artifact_type_enum",
        "vendor_enum",
    ):
        op.execute(f"DROP TYPE IF EXISTS {e}")
