"""Assemble py-lib-testkit config from `pyproject.toml` tables."""

from __future__ import annotations

from py_lib_testkit._api.defaults import DEFAULT_LOGGING_LOCAL_LEVEL
from py_lib_testkit._internal.config.models import ProjectToolingConfig
from py_lib_testkit._internal.config.validation import (
    normalize_package_names,
    optional_runtime_logging_table,
    optional_string,
    optional_string_tuple,
    require_string,
    require_table,
)

_TOOL_TABLE = "ternforge"


def build_project_tooling_config(
    raw_pyproject: dict[str, object],
) -> ProjectToolingConfig:
    """Return validated project tooling config from raw pyproject data."""
    project = require_table(raw_pyproject, "project")
    tool = require_table(raw_pyproject, "tool")
    tooling = require_table(tool, _TOOL_TABLE, table_name=f"tool.{_TOOL_TABLE}")
    runtime_logging = optional_runtime_logging_table(tool)
    return ProjectToolingConfig(
        distribution_name=require_string(project, "name"),
        distribution_version=require_string(project, "version"),
        primary_package=require_string(tooling, "primary_package"),
        package_names=normalize_package_names(tooling.get("package_names")),
        env_prefix=require_string(tooling, "env_prefix"),
        logging_default_local_level=optional_string(
            runtime_logging,
            "default_local_level",
            default=DEFAULT_LOGGING_LOCAL_LEVEL,
        ),
        logging_quiet_module_names=optional_string_tuple(
            runtime_logging.get("quiet_module_names"),
            field_name="quiet_module_names",
        ),
    )
