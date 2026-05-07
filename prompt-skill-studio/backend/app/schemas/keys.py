from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.vendor_keys import Vendor


class KeyCreate(BaseModel):
    vendor: Vendor
    label: str = Field(min_length=1, max_length=120)
    api_key: str = Field(min_length=8, max_length=4096)


class KeyOut(BaseModel):
    id: uuid.UUID
    vendor: Vendor
    label: str
    fingerprint: str
    created_at: datetime
    last_used_at: datetime | None
