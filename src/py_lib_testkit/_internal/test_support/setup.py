"""Reusable async and pytest-process setup helpers.

Use `configure_pytest_process()` from `tests/conftest.py`; `run_async()` supports
interactive callers that already own an event loop.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from pathlib import Path

from py_lib_runtime import set_module_log_levels

from py_lib_testkit._internal.config import get_project_tooling_config

# ================================================================================
# Setup Entry Points
# ================================================================================


def run_async[T](awaitable: Awaitable[T]) -> T:
    """Run one coroutine in normal and already-running loop contexts."""
    _apply_nest_asyncio_if_available()
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(awaitable)
    return loop.run_until_complete(awaitable)


def configure_pytest_process(*, start: Path | None = None) -> None:
    """Keep the repo's package logs quiet during pytest runs."""
    config = get_project_tooling_config(start=start)
    set_module_log_levels({config.primary_package: "WARNING"})


# ================================================================================
# Runtime Helpers
# ================================================================================


def _apply_nest_asyncio_if_available() -> None:
    """Patch the active event loop in interactive/direct-run environments."""
    try:
        import nest_asyncio
    except ModuleNotFoundError:
        return
    nest_asyncio.apply()
