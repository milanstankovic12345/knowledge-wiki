"""Fetch a public article URL and store it as a raw Markdown capture (SSRF-safe)."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import httpx
import trafilatura

from scripts.config import Vault
from scripts.extractors.tools import ExtractionError
from scripts.security import UrlRejected, resolve_host, validate_url
from scripts.storage import dump_frontmatter, slugify

ALLOWED_TYPES = ("text/html", "application/xhtml+xml", "text/plain")
USER_AGENT = "knowledge-wiki/0.1 (personal article capture)"


@dataclass
class Fetched:
    url: str  # final URL after redirects
    html: str


def _pinned(url: str, host: str, ip: str) -> tuple[str, dict[str, str], dict[str, str]]:
    """Connect to the validated IP so a second DNS answer cannot redirect us inside."""
    parts = urlsplit(url)
    netloc = f"[{ip}]" if ":" in ip else ip
    if parts.port:
        netloc += f":{parts.port}"
    host_header = host + (f":{parts.port}" if parts.port else "")
    return (
        parts._replace(netloc=netloc).geturl(),
        {"Host": host_header, "User-Agent": USER_AGENT},
        {"sni_hostname": host},
    )


def fetch_page(
    url: str,
    vault: Vault,
    resolver: Callable[[str], list[str]] = resolve_host,
    transport: httpx.BaseTransport | None = None,
) -> Fetched:
    limits = vault.settings.get("limits", {})
    max_bytes = int(limits.get("max_download_mb", 50)) * 1024 * 1024
    max_redirects = int(limits.get("max_redirects", 3))
    timeout = float(limits.get("url_timeout_seconds", 20))

    with httpx.Client(transport=transport, timeout=timeout, follow_redirects=False) as client:
        for _ in range(max_redirects + 1):
            _, host, ips = validate_url(url, resolver)
            target, headers, extensions = _pinned(url, host, ips[0])
            try:
                with client.stream(
                    "GET", target, headers=headers, extensions=extensions
                ) as response:
                    if response.is_redirect:
                        location = response.headers.get("location", "")
                        if not location:
                            raise ExtractionError("redirect without a location")
                        url = urljoin(url, location)
                        continue
                    response.raise_for_status()
                    kind = response.headers.get("content-type", "").split(";")[0].strip().lower()
                    if kind not in ALLOWED_TYPES:
                        raise ExtractionError(f"unsupported content type {kind or 'unknown'!r}")
                    body = bytearray()
                    for chunk in response.iter_bytes():
                        body.extend(chunk)
                        if len(body) > max_bytes:
                            raise ExtractionError("response is larger than the download limit")
                    encoding = response.encoding or "utf-8"
                    return Fetched(url, bytes(body).decode(encoding, errors="replace"))
            except httpx.HTTPError as exc:
                raise ExtractionError(f"download failed: {type(exc).__name__}") from exc
    raise ExtractionError("too many redirects")


def capture_article(
    url: str,
    vault: Vault,
    resolver: Callable[[str], list[str]] = resolve_host,
    transport: httpx.BaseTransport | None = None,
    privacy: str = "",
) -> Path:
    """Download `url` and write `raw/articles/<title>-<hash8>.md`. Existing captures are kept."""
    page = fetch_page(url, vault, resolver, transport)
    markdown = trafilatura.extract(
        page.html, output_format="markdown", url=page.url, include_comments=False
    )
    if not markdown or not markdown.strip():
        raise ExtractionError("no article text found at that URL")
    meta = trafilatura.extract_metadata(page.html, default_url=page.url)
    title = (getattr(meta, "title", "") or "").strip() or urlsplit(page.url).netloc
    author = (getattr(meta, "author", "") or "").strip()

    digest = hashlib.sha256(markdown.encode("utf-8")).hexdigest()[:8]
    out = vault.path("raw") / "articles" / f"{slugify(title)}-{digest}.md"
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        front = {
            "title": title,
            "source_type": "article",
            "source_url": page.url,
            "author": author,
            "captured_at": date.today().isoformat(),
        }
        if privacy:
            front["privacy"] = privacy
        out.write_text(dump_frontmatter(front, markdown + "\n"), encoding="utf-8")
    return out


__all__ = ["UrlRejected", "capture_article", "fetch_page"]
