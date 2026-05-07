from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import random
from dataclasses import dataclass

import httpx

from app.core.config import get_settings

log = logging.getLogger(__name__)

USER_AGENT = "PromptSkillStudio/0.1 (+https://github.com/Morlock52/ai-document-processor)"


@dataclass(frozen=True)
class FetchResult:
    status: int
    body: str | None
    content_hash: str | None
    error: str | None


async def fetch(url: str, *, timeout: float = 10.0, retries: int = 2) -> FetchResult:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/plain, text/html;q=0.9, application/xml;q=0.8, */*;q=0.5",
    }
    last_exc: Exception | None = None
    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout, headers=headers) as client:
        for attempt in range(retries + 1):
            try:
                resp = await client.get(url)
                if resp.status_code >= 500 or resp.status_code == 429:
                    if attempt < retries:
                        await asyncio.sleep(2 ** attempt + random.random())
                        continue
                if resp.status_code != 200:
                    return FetchResult(resp.status_code, None, None, None)
                body = resp.text
                h = hashlib.sha256(body.encode("utf-8")).hexdigest()
                return FetchResult(200, body, h, None)
            except (httpx.TimeoutException, httpx.HTTPError) as exc:
                last_exc = exc
                if attempt < retries:
                    await asyncio.sleep(2 ** attempt + random.random())
                    continue
                return FetchResult(0, None, None, str(exc))
    return FetchResult(0, None, None, str(last_exc) if last_exc else "unknown")


def write_blob(vendor: str, slug: str, content_hash: str, body: str) -> str:
    base = os.path.join(get_settings().blob_dir, "docs", vendor, slug)
    os.makedirs(base, exist_ok=True)
    path = os.path.join(base, f"{content_hash}.txt")
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)
    return path


def read_blob(path: str) -> str | None:
    if not path or not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return f.read()
