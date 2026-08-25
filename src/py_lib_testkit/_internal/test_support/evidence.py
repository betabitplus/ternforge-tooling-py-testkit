"""Rich evidence publication for interactive and persisted test output.

Why:
    Lets one verified result feed the two standard viewers used by Ternforge:
    IPython for interactive inspection and Allure for persisted reports.
"""

from __future__ import annotations

import base64
import json
import mimetypes
from importlib import import_module
from pathlib import Path
from types import ModuleType

from IPython.core.getipython import get_ipython
from IPython.display import HTML, JSON, FileLink, Image, Video, display

_ALLURE_IMAGE_DIFF = "application/vnd.allure.image.diff"


def publish_json(name: str, payload: object) -> None:
    """Publish one explicitly JSON-serializable value as rich evidence."""
    encoded = json.dumps(payload, indent=2, ensure_ascii=False)
    if get_ipython() is not None:
        display(JSON(payload, expanded=True))
    allure = _load_allure()
    if allure is not None:
        allure.attach(
            encoded,
            name=name,
            attachment_type="application/json",
            extension="json",
        )


def publish_file(
    name: str,
    path: str | Path,
    *,
    media_type: str | None = None,
) -> None:
    """Publish one existing file using its explicit or inferred MIME type."""
    source = Path(path)
    if not source.is_file():
        msg = f"Evidence file does not exist: {source}"
        raise FileNotFoundError(msg)
    resolved_media_type = media_type or mimetypes.guess_type(source.name)[0]
    if resolved_media_type is None:
        resolved_media_type = "application/octet-stream"

    if get_ipython() is not None:
        _display_file(source, resolved_media_type)

    allure = _load_allure()
    if allure is not None:
        suffix = source.suffix.removeprefix(".") or None
        allure.attach.file(
            str(source),
            name=name,
            attachment_type=resolved_media_type,
            extension=suffix,
        )


def publish_visual_diff(
    name: str,
    *,
    expected: str | Path,
    actual: str | Path,
    diff: str | Path,
) -> None:
    """Publish an Allure-compatible Expected/Actual/Diff image comparison."""
    expected_path = _require_png(expected)
    actual_path = _require_png(actual)
    diff_path = _require_png(diff)

    if get_ipython() is not None:
        display(Image(filename=str(expected_path)))
        display(Image(filename=str(actual_path)))
        display(Image(filename=str(diff_path)))

    payload = {
        "expected": _png_data_url(expected_path),
        "actual": _png_data_url(actual_path),
        "diff": _png_data_url(diff_path),
    }
    allure = _load_allure()
    if allure is not None:
        allure.attach(
            json.dumps(payload, separators=(",", ":")),
            name=name,
            attachment_type=_ALLURE_IMAGE_DIFF,
            extension="json",
        )


def _load_allure() -> ModuleType | None:
    """Return Allure when its adapter is installed, otherwise no-op."""
    try:
        return import_module("allure")
    except ModuleNotFoundError:
        return None


def _display_file(path: Path, media_type: str) -> None:
    """Render one file through the most specific IPython display object."""
    if media_type.startswith("image/"):
        display(Image(filename=str(path)))
    elif media_type.startswith("video/"):
        display(Video(filename=str(path), embed=True, mimetype=media_type))
    elif media_type == "application/json":
        display(JSON(filename=str(path), expanded=True))
    elif media_type == "text/html":
        display(HTML(filename=str(path)))
    else:
        display(FileLink(str(path)))


def _require_png(path: str | Path) -> Path:
    """Return one existing PNG path for the Allure visual-diff contract."""
    source = Path(path)
    if not source.is_file():
        msg = f"Visual-diff image does not exist: {source}"
        raise FileNotFoundError(msg)
    if source.suffix.lower() != ".png":
        msg = f"Visual-diff evidence must use PNG files: {source}"
        raise ValueError(msg)
    return source


def _png_data_url(path: Path) -> str:
    """Encode a PNG using Allure's standard visual-diff data-URL shape."""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
