# %%
"""Exercise the public config-loading boundary end to end."""

from __future__ import annotations

from pathlib import Path

from py_lib_testkit import get_project_tooling_config


def test_public_config_pipeline(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """[project]
name = "sample-lib"
version = "1.2.3"

[tool.ternforge]
primary_package = "sample_lib"
package_names = [ "sample_lib" ]
env_prefix = "SAMPLE_LIB"
""",
        encoding="utf-8",
    )

    config = get_project_tooling_config(start=tmp_path)

    assert config.distribution_name == "sample-lib"
    assert config.primary_package == "sample_lib"
