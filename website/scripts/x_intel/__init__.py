"""X intel pipeline package.

The legacy pipeline has functions that call across domain boundaries. During the
modularization migration, the package wires module globals together once so old
entrypoints keep behavior while each domain lives in a real importable module.
"""

from __future__ import annotations

from . import bootstrap, editorial, sources, feedback_feed

_MODULES = (bootstrap, editorial, sources, feedback_feed)


def _public_namespace() -> dict[str, object]:
    names: dict[str, object] = {}
    for module in _MODULES:
        names.update({k: v for k, v in vars(module).items() if not k.startswith("__")})
    return names


def wire_legacy_globals() -> dict[str, object]:
    names = _public_namespace()
    for module in _MODULES:
        module.__dict__.update(names)
    globals().update(names)
    return names


wire_legacy_globals()

__all__ = sorted(k for k in _public_namespace() if not k.startswith("_"))
