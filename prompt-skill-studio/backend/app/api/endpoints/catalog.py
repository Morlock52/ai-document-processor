from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.redis_client import get_redis
from app.core.security import require_session
from app.models.catalog import CatalogKind, VendorCatalog, VendorChangelog
from app.models.vendor_keys import Vendor
from app.services.docs.sources import SOURCES

router = APIRouter(prefix="/catalog", tags=["catalog"], dependencies=[Depends(require_session)])


class CatalogEntryOut(BaseModel):
    vendor: Vendor
    kind: CatalogKind
    slug: str
    name: str
    props: dict
    source_url: str
    captured_at: str


class ChangeEntryOut(BaseModel):
    vendor: Vendor
    source_url: str
    fetched_at: str
    status_code: int
    summary: str | None
    diff: str | None


class StaleSummary(BaseModel):
    vendor: Vendor
    stale_since: str | None


@router.get("/sources")
def list_sources() -> list[dict]:
    return [
        {"vendor": s.vendor.value, "slug": s.slug, "url": s.url, "parser": s.parser}
        for s in SOURCES
    ]


@router.get("/entries", response_model=list[CatalogEntryOut])
def entries(
    vendor: Vendor | None = None,
    kind: CatalogKind | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[CatalogEntryOut]:
    # Latest row per (vendor, slug).
    sub = (
        select(
            VendorCatalog.vendor,
            VendorCatalog.slug,
            func.max(VendorCatalog.captured_at).label("max_at"),
        )
        .group_by(VendorCatalog.vendor, VendorCatalog.slug)
        .subquery()
    )
    q = (
        select(VendorCatalog)
        .join(
            sub,
            (VendorCatalog.vendor == sub.c.vendor)
            & (VendorCatalog.slug == sub.c.slug)
            & (VendorCatalog.captured_at == sub.c.max_at),
        )
        .order_by(VendorCatalog.vendor, VendorCatalog.kind, VendorCatalog.name)
        .limit(limit)
    )
    if vendor:
        q = q.where(VendorCatalog.vendor == vendor)
    if kind:
        q = q.where(VendorCatalog.kind == kind)
    rows = db.execute(q).scalars().all()
    return [
        CatalogEntryOut(
            vendor=r.vendor,
            kind=r.kind,
            slug=r.slug,
            name=r.name,
            props=r.props or {},
            source_url=r.source_url,
            captured_at=r.captured_at.isoformat(),
        )
        for r in rows
    ]


@router.get("/changes", response_model=list[ChangeEntryOut])
def changes(
    vendor: Vendor | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[ChangeEntryOut]:
    q = select(VendorChangelog).order_by(desc(VendorChangelog.fetched_at)).limit(limit)
    if vendor:
        q = q.where(VendorChangelog.vendor == vendor)
    rows = db.execute(q).scalars().all()
    return [
        ChangeEntryOut(
            vendor=r.vendor,
            source_url=r.source_url,
            fetched_at=r.fetched_at.isoformat(),
            status_code=r.status_code,
            summary=r.summary,
            diff=r.diff,
        )
        for r in rows
    ]


@router.get("/stale", response_model=list[StaleSummary])
def stale_status() -> list[StaleSummary]:
    r = get_redis()
    out: list[StaleSummary] = []
    for v in Vendor:
        ts = r.get(f"stale:{v.value}")
        out.append(StaleSummary(vendor=v, stale_since=ts))
    return out
