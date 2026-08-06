"""Project tooling config tests.

Why:
    Protects the pyproject-backed manifest used by shared py-lib tooling for
    package names, environment variables, and runtime logging policy.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from py_lib_testkit import __version__
from py_lib_testkit._internal.config import get_project_tooling_config, get_repo_root

# =============================================================================
# Tests
# =============================================================================


def test_project_config_loads_from_current_repo() -> None:
    config = get_project_tooling_config(start=Path(__file__))

    assert config.distribution_name == "py-lib-testkit"
    assert config.distribution_version == __version__
    assert config.primary_package == "py_lib_testkit"
    assert config.package_names == ("py_lib_testkit",)
    assert config.library_lane == "standard-lib"
    assert config.env_prefix == "PY_LIB_TESTKIT"
    assert config.logging_default_local_level == "DEBUG"
    assert config.logging_quiet_module_names is None


def test_project_config_loads_optional_tooling_and_runtime_policy(
    tmp_path: Path,
) -> None:
    tmp_path.joinpath("pyproject.toml").write_text(
        "\n".join(
            [
                "[project]",
                'name = "sample-lib"',
                'version = "1.2.3"',
                "",
                "[tool.ternforge]",
                'primary_package = "sample_lib"',
                'package_names = [ "sample_lib" ]',
                'library_lane = "standard-lib"',
                'env_prefix = "SAMPLE_LIB"',
                "",
                "[tool.py_lib_runtime.logging]",
                'default_local_level = "INFO"',
                'quiet_module_names = [ "httpx", "urllib3" ]',
                "",
            ]
        ),
        encoding="utf-8",
    )

    config = get_project_tooling_config(start=tmp_path)

    assert config.library_lane == "standard-lib"
    assert config.logging_default_local_level == "INFO"
    assert config.logging_quiet_module_names == ("httpx", "urllib3")


def test_project_config_defaults_library_lane_for_existing_repos(
    tmp_path: Path,
) -> None:
    _write_minimal_pyproject(tmp_path)

    config = get_project_tooling_config(start=tmp_path)

    assert config.library_lane == "standard-lib"


def test_project_config_rejects_unknown_library_lane(tmp_path: Path) -> None:
    _write_minimal_pyproject(tmp_path)
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_text = pyproject_path.read_text(encoding="utf-8")
    pyproject_path.write_text(
        pyproject_text.replace(
            'env_prefix = "SAMPLE_LIB"',
            'library_lane = "bespoke-lib"\nenv_prefix = "SAMPLE_LIB"',
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="library_lane"):
        get_project_tooling_config(start=tmp_path)


def test_repo_root_follows_current_directory_after_cache_warmup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_nested = first_root / "nested"
    second_nested = second_root / "nested"
    first_nested.mkdir(parents=True)
    second_nested.mkdir(parents=True)
    _write_minimal_pyproject(first_root)
    _write_minimal_pyproject(second_root)

    monkeypatch.chdir(first_nested)
    assert get_repo_root() == first_root

    monkeypatch.chdir(second_nested)
    assert get_repo_root() == second_root


def test_project_config_rejects_missing_pyproject(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        get_project_tooling_config(start=tmp_path)


def test_project_config_rejects_missing_tooling_table(tmp_path: Path) -> None:
    tmp_path.joinpath("pyproject.toml").write_text(
        "\n".join(
            [
                "[project]",
                'name = "sample-lib"',
                'version = "1.2.3"',
                "",
                "[tool.ruff]",
                'target-version = "py313"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(TypeError, match=r"\[tool\.ternforge\]"):
        get_project_tooling_config(start=tmp_path)


# =============================================================================
# Helpers
# =============================================================================


def _write_minimal_pyproject(project_root: Path) -> None:
    """Write a minimal py-lib tooling manifest for config discovery tests."""
    project_root.joinpath("pyproject.toml").write_text(
        "\n".join(
            [
                "[project]",
                'name = "sample-lib"',
                'version = "1.2.3"',
                "",
                "[tool.ternforge]",
                'primary_package = "sample_lib"',
                'package_names = [ "sample_lib" ]',
                'env_prefix = "SAMPLE_LIB"',
                "",
            ]
        ),
        encoding="utf-8",
    )
