"""VCR test-support helper tests.

Why:
    Protects shared VCR helpers from import-time repo discovery while keeping
    repo-scoped environment names resolved at the call boundary.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from types import ModuleType

import pytest

# =============================================================================
# Tests
# =============================================================================


def test_vcr_support_imports_are_independent_of_current_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    _fresh_module("py_lib_testkit._internal.test_support.e2e_vcr_guard")
    _fresh_module("py_lib_testkit._internal.test_support._vcr_shared")


def test_multipart_signature_prefix_resolves_from_active_repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_pyproject(tmp_path)
    monkeypatch.chdir(tmp_path)
    shared = _fresh_module("py_lib_testkit._internal.test_support._vcr_shared")

    assert shared.multipart_signature_prefix() == b"SAMPLE_LIB_MULTIPART_SIGNATURE:"


def test_vcr_guard_uses_repo_scoped_recording_env_var(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_pyproject(tmp_path)
    test_file = tmp_path / "tests" / "sample_lib" / "e2e" / "test_case.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("", encoding="utf-8")
    monkeypatch.setenv("SAMPLE_LIB_RECORD_VCR", "1")
    guard = _fresh_module("py_lib_testkit._internal.test_support.e2e_vcr_guard")

    guard.require_vcr_cassette_or_record_mode(
        test_file=str(test_file),
        test_name="test_case",
    )


# =============================================================================
# Helpers
# =============================================================================


def _fresh_module(module_name: str) -> ModuleType:
    """Import one VCR helper module after the test has selected its cwd."""
    module = importlib.import_module(module_name)
    return importlib.reload(module)


def _write_pyproject(project_root: Path) -> None:
    """Write a minimal py-lib project manifest for VCR helper tests."""
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
