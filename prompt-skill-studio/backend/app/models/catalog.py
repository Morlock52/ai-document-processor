from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models._base import Base, TimestampMixin, UUIDMixin
from app.models.vendor_keys import Vendor


class CatalogKind(str, enum.Enum):
    model = "model"
    feature = "feature"
    beta = "beta"
    technique = "technique"
    pricing = "pricing"


class VendorCatalog(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "vendor_catalog"
    __table_args__ = (UniqueConstraint("vendor", "slug", "content_hash", name="uq_catalog_vsh"),)

    vendor: Mapped[Vendor] = mapped_column(Enum(Vendor, name="vendor_enum"), nullable=False)
    kind: Mapped[CatalogKind] = mapped_column(
        Enum(CatalogKind, name="catalog_kind_enum"), nullable=False
    )
    slug: Mapped[str] = mapped_column(String(200), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    props: Mapped[dict] = mapped_column(JSONB, default=dict)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class VendorChangelog(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "vendor_changelog"

    vendor: Mapped[Vendor] = mapped_column(Enum(Vendor, name="vendor_enum"), nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_blob_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    diff: Mapped[str | None] = mapped_column(Text, nullable=True)
