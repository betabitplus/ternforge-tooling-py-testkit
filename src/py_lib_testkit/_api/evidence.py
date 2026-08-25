"""Public rich-evidence facade for executable specifications and tests."""

from __future__ import annotations

from pathlib import Path

from py_lib_testkit._internal import (
    publish_file as _publish_file,
    publish_json as _publish_json,
    publish_visual_diff as _publish_visual_diff,
)


def json(name: str, payload: object) -> None:
    """Show and persist one explicitly JSON-serializable evidence value."""
    _publish_json(name, payload)


def file(
    name: str,
    path: str | Path,
    *,
    media_type: str | None = None,
) -> None:
    """Show and persist one file using its explicit or inferred MIME type."""
    _publish_file(name, path, media_type=media_type)


def visual_diff(
    name: str,
    *,
    expected: str | Path,
    actual: str | Path,
    diff: str | Path,
) -> None:
    """Show and persist an Allure Expected/Actual/Diff image comparison."""
    _publish_visual_diff(
        name,
        expected=expected,
        actual=actual,
        diff=diff,
    )
