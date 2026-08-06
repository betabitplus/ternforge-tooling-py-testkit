"""Reusable direct-run and test-process setup helpers.

Why:
    Pytest runs and direct package-module runs need different setup behavior.

When to use:
    Use `configure_pytest_process()` from `tests/conftest.py`.
    Use `configure_direct_module_process(...)` from package `__init__.py`
    files that support direct module execution.

How:
    Pytest setup lowers logging noise.
    Direct module setup enables nested-event-loop support and package-specific
    logging when needed.

Examples:
    configure_pytest_process()
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import Awaitable
from pathlib import Path
from typing import TypeVar

from py_lib_runtime import (
    build_logging_settings,
    configure_logging,
    set_module_log_levels,
)

from py_lib_testkit._internal.config import get_project_tooling_config

_T = TypeVar("_T")


# ================================================================================
# Setup Entry Points
# ================================================================================


def run_async(awaitable: Awaitable[_T]) -> _T:
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


def configure_direct_module_process(
    *,
    main_file: str | None,
    package_root: Path,
    configure_logging_from_env: str | None = None,
    configure_logging_from_env_suffix: str | None = None,
) -> None:
    """Configure one package for direct `python -m ...` execution."""
    if not _main_file_belongs_to_package(
        main_file=main_file,
        package_root=package_root,
    ):
        return

    _apply_nest_asyncio_if_available()
    if configure_logging_from_env is not None or configure_logging_from_env_suffix:
        config = get_project_tooling_config(start=package_root)
        env_var = configure_logging_from_env or config.env_var(
            configure_logging_from_env_suffix or "LOG_LEVEL"
        )
        settings = build_logging_settings(
            config.primary_package,
            env_prefix=config.env_prefix,
            default_local_level=config.logging_default_local_level,
            quiet_module_names=config.logging_quiet_module_names,
        )
        configure_logging(settings, level=os.getenv(env_var))


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


def _main_file_belongs_to_package(*, main_file: str | None, package_root: Path) -> bool:
    """Return whether `main_file` is a real path inside `package_root`."""
    if not isinstance(main_file, str) or not main_file:
        return False

    main_path = Path(main_file).resolve()
    try:
        main_path.relative_to(package_root.resolve())
    except ValueError:
        return False
    return True
