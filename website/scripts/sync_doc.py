#!/usr/bin/env python3
"""Fetch the source Google Doc via r.jina.ai and build local website data index."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen


DOC_URL = (
    "https://r.jina.ai/https://docs.google.com/document/u/0/d/"
    "1Tch9-CuDa4co2zT6sak318cuJiHHCAXek6SVDrLuShY/mobilebasic"
)


def _unwrap_google_redirect(url: str) -> str:
    try:
        parsed = urlparse(url)
    except ValueError:
        return url
    if "google.com" in parsed.netloc:
        query = parse_qs(parsed.query)
        q = query.get("q")
        if q and q[0]:
            return q[0]
    return url


def _fetch_text(url: str) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; RenaissDocSync/1.0)",
            "Accept": "text/plain, text/markdown;q=0.9, */*;q=0.8",
        },
    )
    with urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _extract_images(markdown_text: str) -> list[dict]:
    pattern = re.compile(r"!\[([^\]]*)\]\((https?://[^)]+)\)")
    items = []
    for idx, (alt, raw_url) in enumerate(pattern.findall(markdown_text), start=1):
        url = _unwrap_google_redirect(raw_url.strip())
        items.append(
            {
                "id": idx,
                "alt": alt.strip() or f"Image {idx}",
                "url": url,
            }
        )
    return items


def _extract_links(markdown_text: str) -> list[str]:
    md_link_pattern = re.compile(r"\[[^\]]+\]\((https?://[^)]+)\)")
    raw_url_pattern = re.compile(r"(?<!\()https?://[^\s)]+")
    urls: list[str] = []
    for raw in md_link_pattern.findall(markdown_text):
        cleaned = raw.strip()
        if not cleaned:
            continue
        urls.append(_unwrap_google_redirect(cleaned))
    for raw in raw_url_pattern.findall(markdown_text):
        cleaned = raw.strip()
        if not cleaned:
            continue
        urls.append(_unwrap_google_redirect(cleaned))

    deduped: list[str] = []
    seen = set()
    for url in urls:
        if not url.startswith("http"):
            continue
        if url in seen:
            continue
        seen.add(url)
        deduped.append(url)
    return deduped


def _extract_headings(markdown_text: str) -> list[str]:
    headings: list[str] = []
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            headings.append(stripped.lstrip("#").strip())
            continue
        if stripped.endswith("指南") or stripped.endswith("介绍") or stripped.endswith("更新"):
            headings.append(stripped)
    seen = set()
    result = []
    for h in headings:
        if h in seen:
            continue
        seen.add(h)
        result.append(h)
    return result


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    md_path = data_dir / "renaiss_full_source.md"
    index_path = data_dir / "renaiss_doc_index.json"

    markdown_text = _fetch_text(DOC_URL)
    md_path.write_text(markdown_text, encoding="utf-8")

    images = _extract_images(markdown_text)
    links = _extract_links(markdown_text)
    headings = _extract_headings(markdown_text)

    payload = {
        "source_url": DOC_URL,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "image_count": len(images),
        "link_count": len(links),
        "heading_count": len(headings),
        "headings": headings[:80],
        "images": images,
        "links": links[:240],
    }
    index_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"synced markdown -> {md_path}")
    print(f"generated index -> {index_path}")
    print(f"images={len(images)} links={len(links)} headings={len(headings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
