#!/usr/bin/env python3
"""Persistent storage helpers for the Renaiss website runtime."""

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path
from typing import Any


def _truthy(value: str, default: bool = False) -> bool:
    raw = str(value or "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def _timestamp() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def _is_empty_dir(path: Path) -> bool:
    try:
        return not any(path.iterdir())
    except Exception:
        return True


def default_data_root(website_root: Path) -> Path:
    app_env = str(os.getenv("APP_ENV") or "").strip().lower()
    if app_env == "server":
        return Path("/data/RENAISS_WEBSITE")
    return website_root / "data"


def get_website_data_dir(website_root: Path) -> Path:
    raw = str(os.getenv("WEBSITE_DATA_ROOT") or "").strip()
    return Path(raw).expanduser().resolve() if raw else default_data_root(website_root).resolve()


def setup_website_storage(website_root: Path) -> dict[str, Any]:
    """Make website/data point at the configured persistent data root.

    This mirrors the Renaiss World pattern: migrate bundled data once when the
    mounted disk is empty, then keep existing relative frontend paths working.
    """

    legacy_data_dir = (website_root / "data").resolve()
    target_root = get_website_data_dir(website_root)
    migrate_once = _truthy(os.getenv("WEBSITE_DATA_MIGRATE_ONCE", "1"), default=True)

    if target_root == legacy_data_dir:
        target_root.mkdir(parents=True, exist_ok=True)
        return {
            "data_dir": str(legacy_data_dir),
            "website_data_root": str(target_root),
            "using_symlink": False,
            "migrated": False,
        }

    target_root.mkdir(parents=True, exist_ok=True)
    migrated = False

    if migrate_once and legacy_data_dir.exists() and not legacy_data_dir.is_symlink() and _is_empty_dir(target_root):
        shutil.copytree(legacy_data_dir, target_root, dirs_exist_ok=True)
        migrated = True
        print(f"[website-storage] migrated initial data: {legacy_data_dir} -> {target_root}")

    if legacy_data_dir.exists() or legacy_data_dir.is_symlink():
        if legacy_data_dir.is_symlink():
            current = (legacy_data_dir.parent / os.readlink(legacy_data_dir)).resolve()
            if current == target_root:
                return {
                    "data_dir": str(legacy_data_dir),
                    "website_data_root": str(target_root),
                    "using_symlink": True,
                    "migrated": migrated,
                }
            legacy_data_dir.unlink()
        else:
            backup_path = legacy_data_dir.parent / f"data_local_backup_{_timestamp()}"
            legacy_data_dir.rename(backup_path)
            print(f"[website-storage] existing local data moved to backup: {backup_path}")

    legacy_data_dir.symlink_to(target_root, target_is_directory=True)
    print(f"[website-storage] linked {legacy_data_dir} -> {target_root}")
    return {
        "data_dir": str(legacy_data_dir),
        "website_data_root": str(target_root),
        "using_symlink": True,
        "migrated": migrated,
    }
