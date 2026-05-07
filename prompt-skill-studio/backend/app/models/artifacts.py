from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import ARRAY, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models._base import Base, TimestampMixin, UUIDMixin
from app.models.vendor_keys import Vendor


class ArtifactType(str, enum.Enum):
    prompt = "prompt"
    skill = "skill"
    agent = "agent"
    mcp = "mcp"


class RunStatus(str, enum.Enum):
    pending = "pending"
    streaming = "streaming"
    completed = "completed"
    failed = "failed"


class McpTransport(str, enum.Enum):
    stdio = "stdio"
    http = "http"
    sse = "sse"


class McpLanguage(str, enum.Enum):
    typescript = "typescript"
    python = "python"


class Prompt(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "prompts"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    body: Mapped[str] = mapped_column(Text, default="")
    variables: Mapped[list] = mapped_column(JSONB, default=list)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    version: Mapped[int] = mapped_column(Integer, default=1)


class Skill(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "skills"

    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    frontmatter: Mapped[dict] = mapped_column(JSONB, default=dict)
    body: Mapped[str] = mapped_column(Text, default="")
    files: Mapped[list] = mapped_column(JSONB, default=list)


class Agent(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "agents"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    vendor: Mapped[Vendor] = mapped_column(Enum(Vendor, name="vendor_enum"), nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    instructions: Mapped[str] = mapped_column(Text, default="")
    tools: Mapped[list] = mapped_column(JSONB, default=list)
    mcp_refs: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), default=list)


class McpServer(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "mcp_servers"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    transport: Mapped[McpTransport] = mapped_column(
        Enum(McpTransport, name="mcp_transport_enum"), nullable=False
    )
    language: Mapped[McpLanguage] = mapped_column(
        Enum(McpLanguage, name="mcp_language_enum"), nullable=False
    )
    tools: Mapped[list] = mapped_column(JSONB, default=list)


class Run(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "runs"

    artifact_type: Mapped[ArtifactType] = mapped_column(
        Enum(ArtifactType, name="artifact_type_enum"), nullable=False
    )
    artifact_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    vendor: Mapped[Vendor] = mapped_column(Enum(Vendor, name="vendor_enum"), nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    input: Mapped[dict] = mapped_column(JSONB, default=dict)
    output: Mapped[str] = mapped_column(Text, default="")
    usage: Mapped[dict] = mapped_column(JSONB, default=dict)
    cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[RunStatus] = mapped_column(
        Enum(RunStatus, name="run_status_enum"), default=RunStatus.pending, nullable=False
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    key_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vendor_keys.id", ondelete="SET NULL"), nullable=True
    )
