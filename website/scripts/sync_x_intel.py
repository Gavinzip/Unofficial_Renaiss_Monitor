#!/usr/bin/env python3
"""Sync 30-day X feed and generate website AI digest JSON."""

from __future__ import annotations

import argparse
import json

from x_intel_core import DEFAULT_ACCOUNTS, sync_accounts


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync X intel feed")
    parser.add_argument(
        "--accounts",
        default=",".join(DEFAULT_ACCOUNTS),
        help="Comma-separated X usernames (without @)",
    )
    parser.add_argument("--days", type=int, default=30, help="Lookback window in days")
    parser.add_argument("--max-posts", type=int, default=12, help="Max posts per account")
    args = parser.parse_args()

    accounts = [x.strip().lstrip("@") for x in args.accounts.split(",") if x.strip()]
    payload = sync_accounts(accounts=accounts, window_days=max(1, args.days), max_posts_per_account=max(1, args.max_posts))

    print(json.dumps(
        {
            "ok": True,
            "generated_at": payload.get("generated_at"),
            "accounts": payload.get("accounts", []),
            "total_cards": payload.get("total_cards", 0),
            "source_stats": payload.get("source_stats", {}),
            "output": "website/data/x_intel_feed.json",
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
