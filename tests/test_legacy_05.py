"""Direct-run and test-process setup helper tests.

Why:
    Protects shared setup helpers from import-time repo discovery while keeping
    dotenv and logging policy resolution scoped to the consuming repository.
"""

from __future__ import annotations

import importlib
import tomllib
from pathlib import Path
from types import ModuleType

import pytest

# =============================================================================
# Tests
# =============================================================================


def test_setup_module_import_is_independent_of_current_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    _fresh_setup_module()


def test_configure_pytest_process_quiets_primary_package(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(_tooling_package_root())
    setup = _fresh_setup_module()
    calls: list[dict[str, str]] = []
    monkeypatch.setattr(setup, "set_module_log_levels", calls.append)

    setup.configure_pytest_process()

    assert calls == [{"py_lib_testkit": "WARNING"}]


def test_configure_direct_module_process_uses_runtime_logging(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_pyproject(tmp_path)
    package_root = tmp_path / "tests" / "sample_lib" / "e2e"
    package_root.mkdir(parents=True)
    main_file = package_root / "test_case.py"
    monkeypatch.chdir(_tooling_package_root())
    setup = _fresh_setup_module()
    settings = object()
    build_calls: list[tuple[tuple[str], dict[str, object]]] = []
    configure_calls: list[tuple[tuple[object], dict[str, str]]] = []
    monkeypatch.setattr(setup, "_apply_nest_asyncio_if_available", lambda: None)
    monkeypatch.setattr(
        setup,
        "build_logging_settings",
        lambda *args, **kwargs: build_calls.append((args, kwargs)) or settings,
    )
    monkeypatch.setattr(
        setup,
        "configure_logging",
        lambda *args, **kwargs: configure_calls.append((args, kwargs)),
    )
    monkeypatch.setenv("SAMPLE_LIB_LOG_LEVEL", "ERROR")

    setup.configure_direct_module_process(
        main_file=str(main_file),
        package_root=package_root,
        configure_logging_from_env_suffix="LOG_LEVEL",
    )

    assert build_calls == [
        (
            ("sample_lib",),
            {
                "default_local_level": "DEBUG",
                "env_prefix": "SAMPLE_LIB",
                "quiet_module_names": None,
            },
        )
    ]
    assert configure_calls == [((settings,), {"level": "ERROR"})]


# =============================================================================
# Helpers
# =============================================================================


def _tooling_package_root() -> Path:
    """Return the repository root for the `py-lib-testkit` distribution."""
    for parent in Path(__file__).resolve().parents:
        pyproject = parent / "pyproject.toml"
        if not pyproject.is_file():
            continue
        with pyproject.open("rb") as stream:
            project = tomllib.load(stream).get("project", {})
        if project.get("name") == "py-lib-testkit":
            return parent
    msg = "Could not locate py-lib-testkit package root."
    raise RuntimeError(msg)


def _write_pyproject(project_root: Path) -> None:
    """Write a minimal py-lib project manifest for setup support tests."""
    project_root.joinpath("pyproject.toml").write_text(
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


def _fresh_setup_module() -> ModuleType:
    """Import setup support after the test has selected the consuming repo."""
    module = importlib.import_module("py_lib_testkit._internal.test_support.setup")
    return importlib.reload(module)
