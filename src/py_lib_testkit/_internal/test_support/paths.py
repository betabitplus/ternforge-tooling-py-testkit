"""Reusable path helpers for the test tree.

Why:
    Centralizes repo-relative path lookup for shared test fixtures and manual
    e2e output locations.

When to use:
    Import from here when test infrastructure needs a stable path inside the
    repository or a module-local test-data directory.
"""

from __future__ import annotations

from pathlib import Path

from py_lib_testkit._internal.config import get_repo_root as _get_repo_root

# ================================================================================
# Path Entry Points
# ================================================================================


def get_repo_root(*, start: Path | None = None) -> Path:
    """Return the repository root directory."""
    return _get_repo_root(start=start)


def get_test_data_path(module_name: str, *, start: Path | None = None) -> Path:
    """Return the `tests/<module_name>/data` directory."""
    return get_repo_root(start=start) / "tests" / module_name / "data"


def get_test_output_dir(
    module_name: str | None = None,
    *,
    start: Path | None = None,
) -> Path:
    """Return the ignored test output directory for a module or repo."""
    output_dir = get_repo_root(start=start) / "tests" / ".outputs"
    if module_name is not None:
        output_dir /= module_name
    return output_dir


def get_test_output_path(
    filename: str,
    *,
    module_name: str | None = None,
    start: Path | None = None,
) -> Path:
    """Return an ignored test output file path."""
    return get_test_output_dir(module_name, start=start) / filename


def get_workbench_output_dir(
    module_name: str | None = None,
    *,
    start: Path | None = None,
) -> Path:
    """Return the ignored workbench output directory for a module or repo."""
    output_dir = get_repo_root(start=start) / "workbench" / ".outputs"
    if module_name is not None:
        output_dir /= module_name
    return output_dir


def get_workbench_output_path(
    filename: str,
    *,
    module_name: str | None = None,
    start: Path | None = None,
) -> Path:
    """Return an ignored workbench output file path."""
    return get_workbench_output_dir(module_name, start=start) / filename
