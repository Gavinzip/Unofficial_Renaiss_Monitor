#!/usr/bin/env python3
"""Run one website data backup."""

from __future__ import annotations

from pathlib import Path

from x_intel_core import load_environment
from website_backup import run_website_backup
from website_storage import get_website_data_dir, setup_website_storage


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    load_environment()
    setup_website_storage(root)
    result = run_website_backup(get_website_data_dir(root), root.parent, reason="manual")
    if result.get("ok"):
        print(f"[website-backup] manual done: changed={bool(result.get('changed'))}")
        return 0
    print(f"[website-backup] manual failed/skipped: {result.get('error') or result.get('reason')}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
