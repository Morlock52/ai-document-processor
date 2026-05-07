from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models._base import Base, TimestampMixin, UUIDMixin


class Vendor(str, enum.Enum):
    anthropic = "anthropic"
    openai = "openai"


class VendorKey(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "vendor_keys"

    vendor: Mapped[Vendor] = mapped_column(Enum(Vendor, name="vendor_enum"), nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(40), nullable=False)
    nonce: Mapped[bytes] = mapped_column(LargeBinary(12), nullable=False)
    ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
