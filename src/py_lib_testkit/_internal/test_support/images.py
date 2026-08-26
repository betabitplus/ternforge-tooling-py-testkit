"""Reusable image helpers for tests and manual workbench probes.

Why:
    Keeps generic Pillow image comparison and ignored-output saving out of
    package-specific test builders.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops

from py_lib_testkit._internal.test_support.paths import get_test_output_path


def image_changed(before: Image.Image, after: Image.Image) -> bool:
    """Return whether two images differ after RGB normalization."""
    return (
        ImageChops.difference(before.convert("RGB"), after.convert("RGB")).getbbox()
        is not None
    )


def save_test_output_image(
    image: Image.Image,
    filename: str,
    *,
    module_name: str | None = None,
) -> Path:
    """Save an image under the ignored test output directory."""
    output_path = get_test_output_path(filename, module_name=module_name)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    return output_path
