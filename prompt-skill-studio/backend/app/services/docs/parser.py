from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

import feedparser
from selectolax.parser import HTMLParser

from app.models.catalog import CatalogKind


@dataclass
class CatalogEntry:
    kind: CatalogKind
    slug: str
    name: str
    props: dict


# Heuristic model-id patterns. Conservative — only well-formed slugs go in.
_MODEL_PATTERNS = [
    re.compile(r"\bclaude-(?:opus|sonnet|haiku)-\d+(?:\.\d+)?(?:-\d{8})?\b"),
    re.compile(r"\bgpt-\d+(?:\.\d+)*(?:-(?:pro|instant|mini|nano|turbo))?\b", re.IGNORECASE),
    re.compile(r"\bo[1-9](?:-(?:pro|mini|nano))?\b"),
]

_LINK_LINE = re.compile(r"^- \[(?P<name>[^\]]+)\]\((?P<url>[^)]+)\)\s*:\s*(?P<desc>.+)$")
_HEADING = re.compile(r"^(?P<level>#{1,3})\s+(?P<title>.+)$")


def _slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:200] or "entry"


def parse_llms_txt(body: str, source_url: str) -> Iterable[CatalogEntry]:
    """Parse the standard `llms.txt` markdown index format."""
    section: str | None = None
    seen: set[str] = set()
    for raw in body.splitlines():
        line = raw.rstrip()
        if not line:
            continue
        h = _HEADING.match(line)
        if h:
            section = h.group("title").strip()
            continue
        m = _LINK_LINE.match(line)
        if m:
            name = m.group("name").strip()
            url = m.group("url").strip()
            desc = m.group("desc").strip()
            slug = _slugify(name)
            if slug in seen:
                continue
            seen.add(slug)
            kind = _classify(section, name, desc)
            yield CatalogEntry(
                kind=kind,
                slug=slug,
                name=name,
                props={"url": url, "section": section, "description": desc},
            )
        else:
            # opportunistic model-id sniff inside narrative text
            for entry in _sniff_models(line):
                if entry.slug not in seen:
                    seen.add(entry.slug)
                    yield entry


def parse_llms_pricing(body: str, source_url: str) -> Iterable[CatalogEntry]:
    """Pricing variants of llms.txt usually contain table-ish lines like
    `gpt-5.5 | 1M ctx | $5 / $30 per 1M tokens`. We do a permissive scan."""
    seen: set[str] = set()
    for line in body.splitlines():
        for entry in _sniff_models(line):
            if entry.slug in seen:
                continue
            seen.add(entry.slug)
            # try to attach pricing if it appears on the same line
            money = re.findall(r"\$([\d.]+)", line)
            ctx = re.search(r"(\d+)\s*[Mm]\b", line) or re.search(r"(\d+)k\b", line)
            if money:
                entry.props["price_usd_per_mtok"] = [float(m) for m in money[:2]]
            if ctx:
                entry.props["context_hint"] = ctx.group(0)
            yield entry


def parse_rss(body: str, source_url: str) -> Iterable[CatalogEntry]:
    feed = feedparser.parse(body)
    for entry in feed.entries[:50]:
        title = getattr(entry, "title", "untitled")
        link = getattr(entry, "link", source_url)
        published = getattr(entry, "published", "") or getattr(entry, "updated", "")
        summary = getattr(entry, "summary", "")
        slug = _slugify(f"changelog-{title}-{published}")
        yield CatalogEntry(
            kind=CatalogKind.feature,
            slug=slug,
            name=title,
            props={"url": link, "published": published, "summary": summary[:1000]},
        )


def parse_html_release_notes(body: str, source_url: str) -> Iterable[CatalogEntry]:
    tree = HTMLParser(body)
    seen: set[str] = set()
    for node in tree.css("h2, h3"):
        title = node.text(strip=True)
        if not title:
            continue
        slug = _slugify(title)
        if slug in seen:
            continue
        seen.add(slug)
        # Pull the next sibling paragraph if present.
        sibling = node.next
        summary = sibling.text(strip=True)[:500] if sibling else ""
        yield CatalogEntry(
            kind=CatalogKind.feature,
            slug=slug,
            name=title,
            props={"url": source_url, "summary": summary},
        )


def _classify(section: str | None, name: str, desc: str) -> CatalogKind:
    haystack = f"{section or ''} {name} {desc}".lower()
    if any(w in haystack for w in ("model", "claude-", "gpt-", " o1", " o3", " o4")):
        return CatalogKind.model
    if any(w in haystack for w in ("beta", "experimental", "preview")):
        return CatalogKind.beta
    if any(w in haystack for w in ("prompt", "best practice", "technique", "engineering")):
        return CatalogKind.technique
    return CatalogKind.feature


def _sniff_models(line: str) -> Iterable[CatalogEntry]:
    for pat in _MODEL_PATTERNS:
        for match in pat.findall(line):
            slug = match.lower()
            yield CatalogEntry(
                kind=CatalogKind.model,
                slug=slug,
                name=match,
                props={"line": line.strip()[:500]},
            )


PARSERS = {
    "llms_txt": parse_llms_txt,
    "llms_pricing": parse_llms_pricing,
    "rss": parse_rss,
    "html_release_notes": parse_html_release_notes,
}
