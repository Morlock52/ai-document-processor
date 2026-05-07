from __future__ import annotations

from dataclasses import dataclass

from app.models.vendor_keys import Vendor


@dataclass(frozen=True)
class DocSource:
    vendor: Vendor
    slug: str
    url: str
    parser: str  # "llms_txt" | "llms_pricing" | "rss" | "html_release_notes"


# Authoritative starting list. Editable; the cron job iterates this.
SOURCES: list[DocSource] = [
    # Anthropic
    DocSource(Vendor.anthropic, "docs-llms", "https://docs.anthropic.com/llms.txt", "llms_txt"),
    DocSource(Vendor.anthropic, "code-llms", "https://code.claude.com/docs/llms.txt", "llms_txt"),
    DocSource(
        Vendor.anthropic,
        "release-notes",
        "https://docs.anthropic.com/en/release-notes/overview",
        "html_release_notes",
    ),
    # OpenAI
    DocSource(Vendor.openai, "platform-llms", "https://platform.openai.com/docs/llms.txt", "llms_txt"),
    DocSource(
        Vendor.openai,
        "developers-llms-full",
        "https://developers.openai.com/api/llms-full.txt",
        "llms_txt",
    ),
    DocSource(
        Vendor.openai,
        "developers-pricing",
        "https://developers.openai.com/api/llms-models-pricing.txt",
        "llms_pricing",
    ),
    DocSource(
        Vendor.openai,
        "changelog-rss",
        "https://developers.openai.com/changelog/rss.xml",
        "rss",
    ),
]
