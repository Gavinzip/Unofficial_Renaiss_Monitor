#!/usr/bin/env python3
"""Git backup scheduler for website runtime data."""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote
from zoneinfo import ZoneInfo


_RUNNING = False
_LAST_RUN_MINUTE_KEY = ""
_TIMER_STARTED = False


def _truthy(value: str, default: bool = False) -> bool:
    raw = str(value or "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def _mask_secret(text: str) -> str:
    pat = str(os.getenv("WEBSITE_BACKUP_PAT") or "")
    raw = str(text or "")
    return raw.replace(pat, "***") if pat else raw


def _backup_enabled() -> bool:
    return _truthy(os.getenv("WEBSITE_BACKUP_ENABLED", "0"))


def _backup_branch() -> str:
    return str(os.getenv("WEBSITE_BACKUP_BRANCH") or "main").strip() or "main"


def _backup_subdir(data_root: Path) -> str:
    return str(os.getenv("WEBSITE_BACKUP_SUBDIR") or data_root.name or "RENAISS_WEBSITE").strip() or "RENAISS_WEBSITE"


def _backup_repo_dir(data_root: Path) -> Path:
    raw = str(os.getenv("WEBSITE_BACKUP_REPO_DIR") or "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return (data_root.parent / ".renaiss_website_data_repo").resolve()


def _resolve_repo_url() -> str:
    repo = str(os.getenv("WEBSITE_BACKUP_REPO") or "").strip()
    pat = str(os.getenv("WEBSITE_BACKUP_PAT") or "").strip()
    if not repo:
        return ""
    if "x-access-token:" in repo:
        return repo
    if pat and repo.startswith("https://github.com/"):
        return repo.replace("https://github.com/", f"https://x-access-token:{quote(pat, safe='')}@github.com/", 1)
    return repo


def _run_git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(["git", *args], cwd=str(cwd), text=True, capture_output=True)
    if result.returncode != 0:
        raw = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {_mask_secret(raw)}")
    return (result.stdout or "").strip()


def _remote_has_branch(repo_url: str, branch: str) -> bool:
    result = subprocess.run(["git", "ls-remote", "--heads", repo_url, branch], text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"git ls-remote failed: {_mask_secret(result.stderr or result.stdout or '')}")
    return bool((result.stdout or "").strip())


def _has_staged_changes(cwd: Path) -> bool:
    result = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=str(cwd), text=True, capture_output=True)
    return result.returncode == 1


def _copytree_clean(source: Path, target: Path, include_volatile: bool) -> None:
    volatile_names = {"x_intel_jobs.json"} if not include_volatile else set()
    shutil.rmtree(target, ignore_errors=True)
    target.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        if item.name in volatile_names or item.name == "__pycache__":
            continue
        dest = target / item.name
        if item.is_dir():
            shutil.copytree(item, dest, symlinks=False)
        else:
            shutil.copy2(item, dest)


def _copy_backup_to_data(source: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for item in target.iterdir():
        if item.name == "__pycache__":
            continue
        if item.is_dir():
            shutil.rmtree(item, ignore_errors=True)
        else:
            try:
                item.unlink()
            except Exception:
                pass
    for item in source.iterdir():
        if item.name == "__pycache__":
            continue
        dest = target / item.name
        if item.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest, symlinks=False)
        else:
            shutil.copy2(item, dest)


def _ensure_repo(repo_url: str, repo_dir: Path, branch: str, project_root: Path) -> None:
    branch_exists = _remote_has_branch(repo_url, branch)
    repo_dir.parent.mkdir(parents=True, exist_ok=True)
    if not (repo_dir / ".git").exists():
        if branch_exists:
            _run_git(["clone", "--branch", branch, "--single-branch", repo_url, str(repo_dir)], project_root)
        else:
            _run_git(["clone", repo_url, str(repo_dir)], project_root)
            _run_git(["checkout", "-B", branch], repo_dir)
    else:
        _run_git(["remote", "set-url", "origin", repo_url], repo_dir)
        if branch_exists:
            _run_git(["fetch", "origin", branch], repo_dir)
            _run_git(["checkout", branch], repo_dir)
            _run_git(["pull", "--ff-only", "origin", branch], repo_dir)
        else:
            _run_git(["checkout", "-B", branch], repo_dir)

    _run_git(["config", "user.name", str(os.getenv("WEBSITE_BACKUP_GIT_NAME") or "Renaiss Website Bot")], repo_dir)
    _run_git(["config", "user.email", str(os.getenv("WEBSITE_BACKUP_GIT_EMAIL") or "bot@renaiss.website")], repo_dir)


def restore_website_data_from_backup(
    data_root: Path,
    project_root: Path,
    *,
    manual: bool = False,
    force_override: bool | None = None,
) -> dict[str, Any]:
    """Restore persistent website data from the configured git backup repo.

    This runs before bundled data migration. It only copies data when the target
    mounted directory is empty unless WEBSITE_DATA_RESTORE_FORCE=1 is set.
    """

    if not manual and not _truthy(os.getenv("WEBSITE_DATA_RESTORE_ON_STARTUP", "1"), default=True):
        return {"ok": True, "restored": False, "reason": "disabled"}

    repo_url = _resolve_repo_url()
    if not repo_url:
        return {"ok": True, "restored": False, "reason": "missing_repo"}
    policy = str(os.getenv("WEBSITE_DATA_RESTORE_POLICY") or "always").strip().lower() or "always"
    force_env = _truthy(os.getenv("WEBSITE_DATA_RESTORE_FORCE", "0"))
    force = bool(force_env if force_override is None else force_override)
    should_require_empty = policy in {"if-empty", "if_empty", "empty-only", "empty_only"}
    if should_require_empty and data_root.exists() and any(data_root.iterdir()) and not force:
        return {"ok": True, "restored": False, "reason": "data_root_not_empty", "policy": policy}

    branch = _backup_branch()
    repo_dir = _backup_repo_dir(data_root)
    subdir = _backup_subdir(data_root)
    try:
        _ensure_repo(repo_url, repo_dir, branch, project_root)
        source = repo_dir / subdir
        if not source.exists() or not source.is_dir():
            return {"ok": False, "restored": False, "reason": "missing_subdir", "subdir": subdir}
        data_root.mkdir(parents=True, exist_ok=True)
        _copy_backup_to_data(source, data_root)
        return {
            "ok": True,
            "restored": True,
            "reason": "restored",
            "branch": branch,
            "subdir": subdir,
            "policy": policy,
            "manual": bool(manual),
            "force": bool(force),
        }
    except Exception as error:
        return {"ok": False, "restored": False, "reason": "restore_failed", "error": _mask_secret(str(error))}


def run_website_backup(data_root: Path, project_root: Path, reason: str = "manual") -> dict[str, Any]:
    global _RUNNING
    manual = str(reason or "").lower().startswith("manual")
    provider = str(os.getenv("WEBSITE_BACKUP_PROVIDER") or "git").strip().lower() or "git"
    if provider != "git":
        return {"ok": False, "skipped": True, "reason": "unsupported_provider", "provider": provider}
    if not _backup_enabled() and not manual:
        return {"ok": False, "skipped": True, "reason": "disabled", "provider": provider}
    if _RUNNING:
        return {"ok": False, "skipped": True, "reason": "already_running", "provider": provider}

    repo_url = _resolve_repo_url()
    if not repo_url:
        return {"ok": False, "skipped": True, "reason": "missing_repo", "provider": provider}
    _RUNNING = True
    try:
        branch = _backup_branch()
        repo_dir = _backup_repo_dir(data_root)
        subdir = _backup_subdir(data_root)
        include_volatile = _truthy(os.getenv("WEBSITE_BACKUP_INCLUDE_VOLATILE", "0"))
        _ensure_repo(repo_url, repo_dir, branch, project_root)
        _copytree_clean(data_root, repo_dir / subdir, include_volatile=include_volatile)
        _run_git(["add", "-A"], repo_dir)
        if not _has_staged_changes(repo_dir):
            return {"ok": True, "changed": False, "reason": reason, "provider": provider, "branch": branch, "subdir": subdir}
        stamp = datetime.utcnow().isoformat(timespec="seconds")
        _run_git(["commit", "-m", f"backup(website): {stamp} [{reason}]"], repo_dir)
        _run_git(["push", "origin", branch], repo_dir)
        return {"ok": True, "changed": True, "reason": reason, "provider": provider, "branch": branch, "subdir": subdir}
    except Exception as error:
        return {"ok": False, "changed": False, "reason": reason, "provider": provider, "error": _mask_secret(str(error))}
    finally:
        _RUNNING = False


def get_website_backup_status(data_root: Path) -> dict[str, Any]:
    repo = str(os.getenv("WEBSITE_BACKUP_REPO") or "").strip()
    return {
        "enabled": _backup_enabled(),
        "provider": str(os.getenv("WEBSITE_BACKUP_PROVIDER") or "git").strip().lower() or "git",
        "has_repo": bool(repo),
        "has_pat": bool(str(os.getenv("WEBSITE_BACKUP_PAT") or "").strip()),
        "branch": _backup_branch(),
        "subdir": _backup_subdir(data_root),
        "repo_dir": str(_backup_repo_dir(data_root)),
        "data_root": str(data_root),
        "timezone": str(os.getenv("WEBSITE_BACKUP_TIMEZONE") or "Asia/Taipei").strip() or "Asia/Taipei",
        "hour": int(str(os.getenv("WEBSITE_BACKUP_HOUR") or "0") or 0),
        "minute": int(str(os.getenv("WEBSITE_BACKUP_MINUTE") or "10") or 10),
        "run_on_startup": _truthy(os.getenv("WEBSITE_BACKUP_RUN_ON_STARTUP", "0")),
        "include_volatile": _truthy(os.getenv("WEBSITE_BACKUP_INCLUDE_VOLATILE", "0")),
    }


def start_website_backup_scheduler(data_root: Path, project_root: Path) -> None:
    global _TIMER_STARTED, _LAST_RUN_MINUTE_KEY
    if _TIMER_STARTED:
        return
    _TIMER_STARTED = True
    status = get_website_backup_status(data_root)
    if not status["enabled"]:
        print("[website-backup] disabled (WEBSITE_BACKUP_ENABLED != 1)")
        return
    if not status["has_repo"]:
        print("[website-backup] disabled: WEBSITE_BACKUP_REPO is empty")
        return
    print(
        "[website-backup] scheduler "
        f"data_root={status['data_root']} repo_dir={status['repo_dir']} "
        f"branch={status['branch']} at {status['hour']:02d}:{status['minute']:02d}"
    )

    def run(reason: str) -> None:
        result = run_website_backup(data_root, project_root, reason=reason)
        if result.get("ok"):
            print(f"[website-backup] {reason} done: changed={bool(result.get('changed'))}")
        else:
            print(f"[website-backup] {reason} failed/skipped: {result.get('error') or result.get('reason')}")

    if status["run_on_startup"]:
        threading.Thread(target=run, args=("startup",), daemon=True).start()

    def loop() -> None:
        global _LAST_RUN_MINUTE_KEY
        tz_name = str(status.get("timezone") or "Asia/Taipei")
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = None
        while True:
            now = datetime.now(tz) if tz else datetime.now()
            key = now.strftime("%Y-%m-%d %H:%M")
            if now.hour == status["hour"] and now.minute == status["minute"] and _LAST_RUN_MINUTE_KEY != key:
                _LAST_RUN_MINUTE_KEY = key
                run("scheduled")
            time.sleep(30)

    threading.Thread(target=loop, daemon=True).start()
