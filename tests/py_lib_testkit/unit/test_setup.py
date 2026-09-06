"""Async and pytest-process setup helper tests.

Protect shared setup helpers from import-time repo discovery while keeping pytest
logging policy resolution scoped to the consuming repository.
"""

from __future__ import annotations

import importlib
import tomllib
from pathlib import Path
from types import ModuleType

import pytest

from py_lib_testkit._internal.test_support import setup as _setup_support_module

# =============================================================================
# Tests
# =============================================================================


def test_setup_module_import_is_independent_of_current_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    _fresh_setup_module()


def test_configure_pytest_process_quiets_primary_package(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(_tooling_package_root())
    setup = _fresh_setup_module()
    calls: list[dict[str, str]] = []
    monkeypatch.setattr(setup, "set_module_log_levels", calls.append)

    setup.configure_pytest_process()

    assert calls == [{"py_lib_testkit": "WARNING"}]


# =============================================================================
# Helpers
# =============================================================================


def _tooling_package_root() -> Path:
    """Return the repository root for the `py-lib-testkit` distribution."""
    for parent in Path(__file__).resolve().parents:
        pyproject = parent / "pyproject.toml"
        if not pyproject.is_file():
            continue
        with pyproject.open("rb") as stream:
            project = tomllib.load(stream).get("project", {})
        if project.get("name") == "py-lib-testkit":
            return parent
    msg = "Could not locate py-lib-testkit package root."
    raise RuntimeError(msg)


def _fresh_setup_module() -> ModuleType:
    """Reload setup support after the test has selected the consuming repo."""
    return importlib.reload(_setup_support_module)
