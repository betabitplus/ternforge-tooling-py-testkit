from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

import py_lib_testkit
from py_lib_testkit import (
    ProjectToolingConfig,
    get_project_tooling_config,
    get_repo_root,
    multipart_signature_prefix,
    run_async,
)


def _write_project(root: Path) -> Path:
    path = root / "pyproject.toml"
    path.write_text(
        """[project]
name = "sample-distribution"
version = "2.3.4"

[tool.ternforge]
primary_package = "sample_lib"
package_names = [ "sample_lib", "sample_extra" ]
env_prefix = "SAMPLE_LIB"

[tool.py_lib_runtime.logging]
default_local_level = "INFO"
quiet_module_names = [ "httpx", "urllib3" ]
""",
        encoding="utf-8",
    )
    return path


def test_public_config_contract_reads_ternforge_table(tmp_path: Path) -> None:
    _write_project(tmp_path)
    config = get_project_tooling_config(start=tmp_path)
    assert isinstance(config, ProjectToolingConfig)
    assert config.distribution_name == "sample-distribution"
    assert config.distribution_version == "2.3.4"
    assert config.primary_package == "sample_lib"
    assert config.package_names == ("sample_lib", "sample_extra")
    assert config.env_prefix == "SAMPLE_LIB"
    assert config.logging_default_local_level == "INFO"
    assert config.logging_quiet_module_names == ("httpx", "urllib3")
    assert config.env_var("LOG_LEVEL") == "SAMPLE_LIB_LOG_LEVEL"
    assert config.record_vcr_var == "SAMPLE_LIB_RECORD_VCR"
    assert config.multipart_signature_prefix == b"SAMPLE_LIB_MULTIPART_SIGNATURE:"


def test_repo_root_walks_up_and_fails_closed(tmp_path: Path) -> None:
    _write_project(tmp_path)
    nested = tmp_path / "tests" / "sample_lib" / "e2e"
    nested.mkdir(parents=True)
    assert get_repo_root(start=nested) == tmp_path
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "pyproject.toml").unlink()
    with pytest.raises(FileNotFoundError):
        get_repo_root(start=outside)


def test_public_exports_include_all_downstream_config_helpers() -> None:
    assert py_lib_testkit.ProjectToolingConfig is ProjectToolingConfig
    assert py_lib_testkit.get_project_tooling_config is get_project_tooling_config
    assert py_lib_testkit.get_repo_root is get_repo_root


def test_multipart_signature_uses_consuming_repository_prefix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert multipart_signature_prefix() == b"SAMPLE_LIB_MULTIPART_SIGNATURE:"


def test_run_async_works_inside_an_active_event_loop() -> None:
    async def nested() -> int:
        await asyncio.sleep(0)
        return 42

    async def outer() -> None:
        assert run_async(nested()) == 42

    asyncio.run(outer())
