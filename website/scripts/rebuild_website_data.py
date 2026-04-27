#!/usr/bin/env python3
"""Rebuild website feed + i18n bundle into the persistent data directory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from website_i18n_runtime import configure_i18n_runtime, rebuild_i18n_bundle_sync
from website_storage import get_website_data_dir
from x_intel_core import load_environment, sync_accounts


ROOT = Path(__file__).resolve().parents[1]


def _read_feed(feed_path: Path) -> dict:
    if not feed_path.exists():
        return {}
    try:
        raw = json.loads(feed_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild website runtime data and i18n bundle")
    parser.add_argument("--langs", default="zh-Hant,zh-Hans,en,ko", help="Comma-separated i18n target langs")
    parser.add_argument("--window-days", type=int, default=30, help="Sync window days for source feed rebuild")
    parser.add_argument("--max-posts-per-account", type=int, default=80, help="Max posts per account during sync")
    parser.add_argument("--skip-sync", action="store_true", help="Only rebuild i18n from existing x_intel_feed.json")
    args = parser.parse_args()

    load_environment()
    data_root = get_website_data_dir(ROOT)
    feed_path = data_root / "x_intel_feed.json"
    configure_i18n_runtime(data_root, feed_path)

    langs = [x.strip() for x in str(args.langs or "").split(",") if x.strip()]
    if not langs:
        langs = ["zh-Hant", "zh-Hans", "en", "ko"]

    if args.skip_sync:
        feed = _read_feed(feed_path)
        if not feed:
            raise RuntimeError(f"missing feed at {feed_path}")
    else:
        feed = sync_accounts(
            accounts=None,
            window_days=max(1, int(args.window_days)),
            max_posts_per_account=max(10, int(args.max_posts_per_account)),
        )

    bundle = rebuild_i18n_bundle_sync(feed, target_langs=langs, force=True)
    bundle_langs = bundle.get("langs") if isinstance(bundle.get("langs"), dict) else {}
    qa = bundle.get("qa") if isinstance(bundle.get("qa"), dict) else {}
    print(f"data_root={data_root}")
    print(
        f"feed.generated_at={feed.get('generated_at')} total_cards={feed.get('total_cards')} "
        f"source_total={feed.get('source_total_cards')} raw_total={feed.get('raw_total_cards')}"
    )
    print(
        f"bundle.version={bundle.get('version')} source_generated_at={bundle.get('source_generated_at')} "
        f"langs={sorted(bundle_langs.keys()) if isinstance(bundle_langs, dict) else []}"
    )
    for tag in langs:
        row = qa.get(tag) if isinstance(qa.get(tag), dict) else {}
        cards = bundle_langs.get(tag) if isinstance(bundle_langs, dict) else {}
        card_rows = cards.get("cards") if isinstance(cards, dict) else []
        print(
            f"[{tag}] cards={len(card_rows) if isinstance(card_rows, list) else 0} "
            f"coverage={row.get('coverage')} mode={row.get('mode')} "
            f"translated={row.get('translated')} total={row.get('total')} pending={row.get('pending_count')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
