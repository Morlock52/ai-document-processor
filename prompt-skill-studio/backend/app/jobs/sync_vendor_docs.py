from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.db import SessionLocal
from app.core.redis_client import get_redis
from app.models.catalog import VendorCatalog, VendorChangelog
from app.services.docs.differ import unified_diff
from app.services.docs.fetcher import fetch, read_blob, write_blob
from app.services.docs.parser import PARSERS
from app.services.docs.sources import SOURCES, DocSource

log = logging.getLogger(__name__)


def sync_vendor_docs() -> dict:
    """Entry point used by RQ. Returns a small summary so admins can see what happened."""
    return asyncio.run(_run())


async def _run() -> dict:
    started = datetime.now(timezone.utc)
    summary = {"started": started.isoformat(), "sources": [], "stale_vendors": []}

    for src in SOURCES:
        result = await _process_source(src)
        summary["sources"].append(result)
        if result["status"] != 200 and result["fresh_rows"] == 0:
            summary["stale_vendors"].append(src.vendor.value)

    # Banner trigger.
    r = get_redis()
    if any(s.get("changed") for s in summary["sources"]):
        r.set("change:latest", started.isoformat(), ex=60 * 60 * 24 * 30)
    for v in set(summary["stale_vendors"]):
        r.set(f"stale:{v}", started.isoformat(), ex=60 * 60 * 24 * 7)

    summary["finished"] = datetime.now(timezone.utc).isoformat()
    return summary


async def _process_source(src: DocSource) -> dict:
    res = await fetch(src.url)
    fetched_at = datetime.now(timezone.utc)

    with SessionLocal() as db:
        prior = db.execute(
            select(VendorChangelog)
            .where(VendorChangelog.source_url == src.url)
            .order_by(desc(VendorChangelog.fetched_at))
            .limit(1)
        ).scalar_one_or_none()
        prior_body = read_blob(prior.raw_blob_path) if prior and prior.raw_blob_path else None

        if res.status != 200 or res.body is None:
            db.add(
                VendorChangelog(
                    vendor=src.vendor,
                    source_url=src.url,
                    fetched_at=fetched_at,
                    status_code=res.status,
                    raw_blob_path=None,
                    summary=res.error or f"non-200: {res.status}",
                    diff=None,
                )
            )
            db.commit()
            return {
                "vendor": src.vendor.value,
                "slug": src.slug,
                "url": src.url,
                "status": res.status,
                "fresh_rows": 0,
                "changed": False,
                "error": res.error,
            }

        # 200 path
        if prior and prior.status_code == 200 and prior.raw_blob_path and prior.raw_blob_path.endswith(f"{res.content_hash}.txt"):
            # No change since last successful capture.
            db.add(
                VendorChangelog(
                    vendor=src.vendor,
                    source_url=src.url,
                    fetched_at=fetched_at,
                    status_code=200,
                    raw_blob_path=prior.raw_blob_path,
                    summary="no change",
                    diff=None,
                )
            )
            db.commit()
            return {
                "vendor": src.vendor.value,
                "slug": src.slug,
                "url": src.url,
                "status": 200,
                "fresh_rows": 0,
                "changed": False,
            }

        blob_path = write_blob(src.vendor.value, src.slug, res.content_hash, res.body)
        diff_text = unified_diff(prior_body, res.body)
        db.add(
            VendorChangelog(
                vendor=src.vendor,
                source_url=src.url,
                fetched_at=fetched_at,
                status_code=200,
                raw_blob_path=blob_path,
                summary=f"updated: {res.content_hash[:8]}",
                diff=diff_text,
            )
        )

        parser = PARSERS.get(src.parser)
        fresh = 0
        if parser:
            for entry in parser(res.body, src.url):
                stmt = (
                    pg_insert(VendorCatalog)
                    .values(
                        vendor=src.vendor,
                        kind=entry.kind,
                        slug=entry.slug,
                        name=entry.name,
                        props=entry.props,
                        source_url=src.url,
                        captured_at=fetched_at,
                        content_hash=res.content_hash,
                    )
                    .on_conflict_do_nothing(constraint="uq_catalog_vsh")
                )
                result = db.execute(stmt)
                if result.rowcount:
                    fresh += 1
        db.commit()

        return {
            "vendor": src.vendor.value,
            "slug": src.slug,
            "url": src.url,
            "status": 200,
            "fresh_rows": fresh,
            "changed": True,
            "content_hash": res.content_hash,
        }


if __name__ == "__main__":
    import json

    print(json.dumps(sync_vendor_docs(), indent=2))
