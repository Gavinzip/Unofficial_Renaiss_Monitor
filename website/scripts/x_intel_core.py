#!/usr/bin/env python3
"""Compatibility entrypoint for the X intel pipeline.

Public imports should continue to use this file for now:
    from x_intel_core import sync_accounts

The implementation lives in the x_intel package modules.
"""

from __future__ import annotations

from x_intel import *  # noqa: F401,F403
