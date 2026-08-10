"""Test-support path helper tests.

Why:
    Protects repo-relative path helpers from import-time repo discovery so
    shared test support remains safe to import from any process location.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from types import ModuleType

import pytest

# =============================================================================
# Tests
# =============================================================================


def test_paths_module_import_is_independent_of_current_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    _fresh_paths_module()


def test_paths_resolve_from_explicit_start_path(tmp_path: Path) -> None:
    _write_pyproject(tmp_path)
    paths = _fresh_paths_module()

    assert paths.get_repo_root(start=tmp_path / "tests") == tmp_path
    assert paths.get_test_data_path("sample_lib", start=tmp_path) == (
        tmp_path / "tests" / "sample_lib" / "data"
    )
    assert paths.get_test_output_path(
        "sample.png",
        module_name="sample_lib",
        start=tmp_path,
    ) == (tmp_path / "tests" / ".outputs" / "sample_lib" / "sample.png")
    assert paths.get_workbench_output_path(
        "result.json",
        module_name="probe",
        start=tmp_path,
    ) == (tmp_path / "workbench" / ".outputs" / "probe" / "result.json")


# =============================================================================
# Helpers
# =============================================================================


def _fresh_paths_module() -> ModuleType:
    """Reload path helpers after the test has selected its cwd."""
    from py_lib_testkit._internal.test_support import paths

    return importlib.reload(paths)


def _write_pyproject(project_root: Path) -> None:
    """Write a minimal py-lib project manifest for path helper tests."""
    project_root.joinpath("pyproject.toml").write_text(
        (
            "[project]\n"
            'name = "sample-lib"\n'
            'version = "1.2.3"\n'
            "\n[tool.ternforge]\n"
            'primary_package = "sample_lib"\n'
            'package_names = [ "sample_lib" ]\n'
            'env_prefix = "SAMPLE_LIB"\n'
        ),
        encoding="utf-8",
    )
