"""Reusable VCR guards for pytest e2e tests.

Why:
    A replay-based e2e test should fail clearly when its cassette is missing
    instead of silently making a live request.

When to use:
    Use inside pytest e2e tests that depend on committed cassettes.

How:
    `require_vcr_cassette_or_record_mode(...)` checks whether the cassette
    exists or recording was explicitly enabled.

Examples:
    require_vcr_cassette_or_record_mode(
        test_file=__file__,
        test_name="test_pipeline",
    )
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from py_lib_testkit._internal.config import get_project_tooling_config

# ================================================================================
# VCR Guard Entry Points
# ================================================================================


def cassette_file_path(*, test_file: str, test_name: str) -> Path:
    """Return the canonical cassette file path for an e2e test function."""
    return (
        Path(test_file).resolve().parent
        / "cassettes"
        / Path(test_file).stem
        / f"{test_name}.yaml"
    )


def require_vcr_cassette_or_record_mode(*, test_file: str, test_name: str) -> None:
    """Fail when replay data is missing and no explicit recording mode is active."""
    cassette_file = cassette_file_path(test_file=test_file, test_name=test_name)
    record_vcr_env_var = get_project_tooling_config(
        start=Path(test_file).resolve(),
    ).record_vcr_var
    if cassette_file.exists():
        return
    if _recording_enabled(record_vcr_env_var):
        return
    if _pytest_record_mode() not in {None, "none"}:
        return
    pytest.fail(
        reason=(
            "VCR cassette missing for e2e test. "
            "Record with pytest `--record-mode=rewrite` or run the script with "
            f"`{record_vcr_env_var}=1`."
        ),
        pytrace=False,
    )


# ================================================================================
# Environment Helpers
# ================================================================================


def _recording_enabled(env_var: str) -> bool:
    """Return whether standalone VCR recording was explicitly enabled."""
    return os.getenv(env_var) == "1"


def _pytest_record_mode() -> str | None:
    """Return pytest's explicit VCR record mode, if provided on the CLI."""
    argv = sys.argv
    for index, arg in enumerate(argv):
        if arg.startswith("--record-mode="):
            return arg.split("=", 1)[1]
        if arg == "--record-mode" and index + 1 < len(argv):
            return argv[index + 1]
    return None
