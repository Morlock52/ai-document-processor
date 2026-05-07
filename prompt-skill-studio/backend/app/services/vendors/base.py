"""Vendor-agnostic streaming contract.

Each adapter is responsible for talking to its SDK, yielding token deltas, and
finalizing with a usage payload. Cost computation lives in `services/pricing.py`
and is fed by `vendor_catalog` rows so that prices stay current automatically.
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any


@dataclass
class StreamFrame:
    kind: str  # "token" | "usage" | "done" | "error"
    data: Any


class VendorAdapter:
    vendor: str = "base"

    async def stream(
        self,
        *,
        api_key: str,
        model: str,
        system: str | None,
        user: str,
        max_tokens: int = 1024,
        extra: dict | None = None,
    ) -> AsyncIterator[StreamFrame]:
        raise NotImplementedError
        yield  # pragma: no cover  -- make this an async generator
