"""Image test-support helper tests.

Why:
    Protects generic image comparison and ignored-output saving helpers used
    by generated py-lib tests and demos.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from types import ModuleType

import pytest
from PIL import Image

# =============================================================================
# Tests
# =============================================================================


def test_image_changed_detects_rgb_differences() -> None:
    images = _fresh_images_module()
    before = Image.new("RGB", (10, 10), color="white")
    after = before.copy()
    after.putpixel((0, 0), (255, 0, 0))

    assert images.image_changed(before, after)
    assert not images.image_changed(before, before.copy())


def test_save_test_output_image_creates_parent_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_pyproject(tmp_path)
    monkeypatch.chdir(tmp_path)
    images = _fresh_images_module()
    image = Image.new("RGB", (2, 2), color="white")

    output_path = images.save_test_output_image(
        image,
        "sample.png",
        module_name="py_lib_testkit",
    )

    assert output_path.is_file()
    assert output_path.name == "sample.png"
    assert output_path.is_relative_to(tmp_path)


# =============================================================================
# Helpers
# =============================================================================


def _fresh_images_module() -> ModuleType:
    """Reload path/image helpers after the test has selected a repo root."""
    from py_lib_testkit._internal.config import state
    from py_lib_testkit._internal.test_support import images, paths

    importlib.reload(state)
    importlib.reload(paths)
    return importlib.reload(images)


def _write_pyproject(project_root: Path) -> None:
    """Write a minimal py-lib project manifest for image helper tests."""
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
