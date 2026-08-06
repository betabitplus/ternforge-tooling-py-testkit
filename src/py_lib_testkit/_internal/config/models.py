"""Config models for py-lib-testkit."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from py_lib_testkit._api.defaults import (
    DEFAULT_LIBRARY_LANE,
    DEFAULT_LOGGING_LOCAL_LEVEL,
    SUPPORTED_LIBRARY_LANES,
)

_TOOL_TABLE = "ternforge"


@dataclass(frozen=True, slots=True)
class ProjectToolingConfig:
    """Typed repo-tooling values loaded from `pyproject.toml`."""

    distribution_name: str
    distribution_version: str
    primary_package: str
    package_names: tuple[str, ...]
    env_prefix: str
    library_lane: str = DEFAULT_LIBRARY_LANE
    logging_default_local_level: str = DEFAULT_LOGGING_LOCAL_LEVEL
    logging_quiet_module_names: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        """Reject empty or internally inconsistent config values."""
        if not self.distribution_name:
            msg = "pyproject.toml [project].name must be a non-empty string."
            raise ValueError(msg)
        if not self.distribution_version:
            msg = "pyproject.toml [project].version must be a non-empty string."
            raise ValueError(msg)
        if not self.package_names:
            msg = (
                f"pyproject.toml [tool.{_TOOL_TABLE}].package_names must contain "
                "at least one package."
            )
            raise ValueError(msg)
        if self.primary_package not in self.package_names:
            msg = (
                f"pyproject.toml [tool.{_TOOL_TABLE}].primary_package must appear "
                "in package_names."
            )
            raise ValueError(msg)
        if self.library_lane not in SUPPORTED_LIBRARY_LANES:
            msg = (
                f"pyproject.toml [tool.{_TOOL_TABLE}].library_lane must be one of "
                f"{', '.join(SUPPORTED_LIBRARY_LANES)}."
            )
            raise ValueError(msg)
        if not self.logging_default_local_level:
            msg = (
                "pyproject.toml [tool.py_lib_runtime.logging]."
                "default_local_level must be a non-empty string."
            )
            raise ValueError(msg)

    @property
    def record_vcr_var(self) -> str:
        """Return the standalone VCR-recording toggle variable for this repo."""
        return self.env_var("RECORD_VCR")

    @property
    def multipart_signature_prefix(self) -> bytes:
        """Return the VCR multipart signature prefix for this repo."""
        return f"{self.env_prefix}_MULTIPART_SIGNATURE:".encode("ascii")

    @property
    def public_contract_forbidden_prefixes(self) -> tuple[str, ...]:
        """Return `_internal` prefixes public-contract tests may not reference."""
        return tuple(f"{package_name}._internal" for package_name in self.package_names)

    def env_var(self, suffix: str) -> str:
        """Return one repo-scoped environment variable name."""
        return f"{self.env_prefix}_{suffix}"

    def public_contract_checked_dirs(
        self,
        *,
        repo_root: Path | None = None,
    ) -> tuple[Path, ...]:
        """Return test trees checked for forbidden `_internal` references."""
        from py_lib_testkit._internal.config.state import get_repo_root

        root = get_repo_root() if repo_root is None else repo_root
        checked_dirs: list[Path] = []
        for package_name in self.package_names:
            checked_dirs.extend(
                [
                    root / "tests" / package_name / "e2e",
                    root
                    / "tests"
                    / package_name
                    / "property_based"
                    / "public_contract",
                    root / "tests" / package_name / "support",
                ]
            )
        return tuple(checked_dirs)
