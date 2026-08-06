"""Load and cache py-lib-testkit config from `pyproject.toml`."""

from __future__ import annotations

import tomllib
from functools import cache
from pathlib import Path

from py_lib_testkit._internal.config.assembly import build_project_tooling_config
from py_lib_testkit._internal.config.models import ProjectToolingConfig

_PYPROJECT_FILE_NAME = "pyproject.toml"


def get_repo_root(*, start: Path | None = None) -> Path:
    """Return the consuming repository root directory."""
    return _pyproject_path(start=_normalize_start(start)).parent


def get_project_tooling_config(*, start: Path | None = None) -> ProjectToolingConfig:
    """Load and cache the shared repo-tooling config."""
    return _get_project_tooling_config(_normalize_start(start))


@cache
def _get_project_tooling_config(start: Path) -> ProjectToolingConfig:
    """Load and cache repo-tooling config for one starting path."""
    with _pyproject_path(start=start).open("rb") as pyproject_file:
        raw_pyproject = tomllib.load(pyproject_file)
    return build_project_tooling_config(raw_pyproject)


@cache
def _pyproject_path(*, start: Path | None = None) -> Path:
    """Return a repo `pyproject.toml` path by walking upward from a start path."""
    start_path = _normalize_start(start)
    candidate_roots = (
        (start_path, *start_path.parents)
        if start_path.is_dir()
        else (start_path.parent, *start_path.parent.parents)
    )
    for candidate_root in candidate_roots:
        candidate_path = candidate_root / _PYPROJECT_FILE_NAME
        if candidate_path.is_file():
            return candidate_path

    msg = f"Could not find {_PYPROJECT_FILE_NAME} above {start_path}."
    raise FileNotFoundError(msg)


def _normalize_start(start: Path | None) -> Path:
    """Return an absolute path to begin repo discovery."""
    if start is None:
        return Path.cwd().resolve()
    return start.expanduser().resolve()
