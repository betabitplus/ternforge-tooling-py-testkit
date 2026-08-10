"""Public Ternforge testkit configuration facade."""

from __future__ import annotations

# pyright: reportUnusedImport=false
from py_lib_testkit._internal.config import (  # noqa: F401
    ProjectToolingConfig,
    get_project_tooling_config,
    get_repo_root,
)
