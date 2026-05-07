from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models._base import Base, TimestampMixin, UUIDMixin


class AppSettings(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "app_settings"

    require_login: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    login_passcode_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
