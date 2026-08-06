"""Shared VCR body comparison helpers.

Why:
    Keeps generic JSON, media, multipart, and diffing logic reusable across
    projects without tying it to one project's provider-specific request rules.

When to use:
    Import from here when a project-specific VCR extension needs common body
    comparison building blocks.

How:
    Use the exported comparison helpers and pass any project-specific string
    normalization as a callback instead of duplicating the low-level logic.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
from collections.abc import Callable, Iterable
from io import BytesIO
from typing import Any

from PIL import Image

from py_lib_testkit._internal.config import get_project_tooling_config

# ================================================================================
# Shared Comparators
# ================================================================================


def compare_optional_multipart_single_file_content(r1: Any, r2: Any) -> bool | None:
    """Compare multipart single-file bodies, if both requests use that shape."""
    content_type_left = get_header_value(r1, "content-type")
    content_type_right = get_header_value(r2, "content-type")
    boundary_left = extract_boundary(content_type_left)
    boundary_right = extract_boundary(content_type_right)
    if not boundary_left or not boundary_right:
        return None

    signature_left = _multipart_single_file_signature(r1, boundary_left)
    signature_right = _multipart_single_file_signature(r2, boundary_right)
    if signature_left is None or signature_right is None:
        return None

    return signature_left == signature_right


def compare_optional_json_bodies(
    r1: Any,
    r2: Any,
    *,
    string_normalizer: Callable[[str], Any] | None = None,
) -> tuple[bool | None, str | None]:
    """Compare JSON request bodies after generic semantic normalization."""
    if not _is_json_request(r1) or not _is_json_request(r2):
        return None, None

    payload_left = normalize_json_body(
        to_bytes(getattr(r1, "body", None)),
        string_normalizer=string_normalizer,
    )
    payload_right = normalize_json_body(
        to_bytes(getattr(r2, "body", None)),
        string_normalizer=string_normalizer,
    )
    if payload_left is None or payload_right is None:
        return None, None
    if payload_left == payload_right:
        return True, None
    return False, describe_first_difference(payload_left, payload_right)


def normalize_json_body(
    body: bytes,
    *,
    string_normalizer: Callable[[str], Any] | None = None,
) -> Any:
    """Parse and normalize one JSON body payload."""
    if not body:
        return None

    payload = json.loads(body.decode("utf-8", errors="strict"))
    return _normalize_json_value(payload, string_normalizer=string_normalizer)


# ================================================================================
# JSON And Media Normalization
# ================================================================================


def to_bytes(value: Any) -> bytes:
    """Convert supported request-body values into bytes."""
    if value is None:
        return b""
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("utf-8")
    return bytes(value)


def normalize_inline_media_bytes(*, mime_type: str, data: bytes) -> dict[str, Any]:
    """Normalize inline media bytes into a stable semantic signature."""
    if mime_type.lower() == "image/png" and is_png(data):
        return png_pixels_signature(data)
    return {
        "kind": "bytes_sha256",
        "sha256": hashlib.sha256(data).hexdigest(),
        "size": len(data),
    }


def parse_data_url(value: str) -> tuple[str, bytes] | None:
    """Parse one base64 data URL into `(mime_type, decoded_bytes)`."""
    if not value.startswith("data:"):
        return None
    header, separator, payload = value.partition(",")
    if separator != "," or ";base64" not in header:
        return None

    mime_type = header[5:].split(";", 1)[0] or "application/octet-stream"
    decoded = decode_base64_bytes(payload)
    if decoded is None:
        return None
    return mime_type, decoded


def decode_base64_bytes(value: str) -> bytes | None:
    """Decode wrapped or URL-safe base64 text into raw bytes."""
    compact = strip_ascii_whitespace(value)
    if not compact:
        return None

    normalized = compact.replace("-", "+").replace("_", "/")
    remainder = len(normalized) % 4
    if remainder == 1:
        return None
    if remainder:
        normalized += "=" * (4 - remainder)

    try:
        return base64.b64decode(normalized, validate=True)
    except (binascii.Error, ValueError):
        return None


def strip_ascii_whitespace(value: str) -> str:
    """Remove ASCII whitespace characters from one string."""
    return "".join(value.split())


def is_png(data: bytes) -> bool:
    """Return whether one byte string starts with the PNG signature."""
    return data.startswith(b"\x89PNG\r\n\x1a\n")


# ================================================================================
# Difference Reporting
# ================================================================================


def describe_first_difference(left: Any, right: Any, path: str = "$") -> str:
    """Describe the first semantic difference between two normalized values."""
    if type(left) is not type(right):
        return (
            f"{path}: type {type(left).__name__} != {type(right).__name__}; "
            f"{_summarize_value(left)} != {_summarize_value(right)}"
        )

    if isinstance(left, dict):
        return _describe_dict_difference(left, right, path)

    if isinstance(left, list):
        return _describe_list_difference(left, right, path)

    return f"{path}: {_summarize_value(left)} != {_summarize_value(right)}"


def multipart_signature_prefix() -> bytes:
    """Return the repo-specific multipart signature prefix used by VCR helpers."""
    return get_project_tooling_config().multipart_signature_prefix


# ================================================================================
# Request And Multipart Helpers
# ================================================================================


def get_header_value(request: Any, name: str) -> str:
    """Read one request header case-insensitively from a VCR-style request."""
    headers = getattr(request, "headers", {}) or {}
    for key, value in _headers_items(headers):
        if str(key).lower() == name.lower():
            return _header_text(value)
    return ""


def _header_text(value: Any) -> str:
    """Return one normalized request-header value."""
    if isinstance(value, list | tuple):
        return str(value[0]) if value else ""
    return str(value)


def extract_boundary(content_type: str) -> str | None:
    """Extract the multipart boundary from one content-type header."""
    if "multipart/form-data" not in content_type.lower():
        return None
    for part in (chunk.strip() for chunk in content_type.split(";")):
        if part.lower().startswith("boundary="):
            return part.split("=", 1)[1].strip().strip('"')
    return None


def extract_single_part_content(body: bytes, boundary: str) -> bytes | None:
    """Extract the raw file content from one multipart single-file body."""
    boundary_bytes = boundary.encode("utf-8")
    if not body.startswith(b"--" + boundary_bytes):
        inferred = _infer_boundary_from_body(body)
        if inferred is None:
            return None
        boundary_bytes = inferred

    prefix = b"--" + boundary_bytes + b"\r\n"
    suffix = b"\r\n--" + boundary_bytes + b"--"
    if not body.startswith(prefix):
        return None

    header_end = body.find(b"\r\n\r\n", len(prefix))
    if header_end == -1:
        return None

    content_start = header_end + 4
    end = body.rfind(suffix)
    if end == -1:
        return None

    content_end = end
    trailing_start = content_end - 2
    if body[trailing_start:content_end] == b"\r\n":
        content_end -= 2
    return body[content_start:content_end]


# ================================================================================
# Binary Content Helpers
# ================================================================================


def png_pixels_signature(png_bytes: bytes) -> dict[str, Any]:
    """Normalize one PNG into a stable pixel-based signature."""
    with Image.open(BytesIO(png_bytes)) as image:
        image.load()
        rgba = image.convert("RGBA")
        return {
            "kind": "png_pixels",
            "size": rgba.size,
            "mode": rgba.mode,
            "sha256": hashlib.sha256(rgba.tobytes()).hexdigest(),
        }


def png_pixels_digest(png_bytes: bytes) -> tuple[tuple[int, int], str, bytes]:
    """Return the raw RGBA pixel digest tuple for one PNG."""
    with Image.open(BytesIO(png_bytes)) as image:
        image.load()
        rgba = image.convert("RGBA")
        return rgba.size, rgba.mode, rgba.tobytes()


# ================================================================================
# Internal Helpers
# ================================================================================


def _is_json_request(request: Any) -> bool:
    """Return whether one request declares a JSON content type."""
    content_type = get_header_value(request, "content-type").lower()
    return "application/json" in content_type


def _multipart_single_file_signature(
    request: Any,
    boundary: str,
) -> dict[str, Any] | None:
    """Return a semantic signature for one multipart single-file body."""
    body_bytes = to_bytes(getattr(request, "body", None))
    cached_signature = _decode_multipart_signature_cache(body_bytes)
    if cached_signature is not None:
        return cached_signature

    content = extract_single_part_content(body_bytes, boundary)
    if content is None:
        return None

    mime_type = "image/png" if is_png(content) else "application/octet-stream"
    return normalize_inline_media_bytes(mime_type=mime_type, data=content)


def _decode_multipart_signature_cache(body: bytes) -> dict[str, Any] | None:
    """Decode a precomputed multipart signature body when present."""
    prefix = multipart_signature_prefix()
    if not body.startswith(prefix):
        return None
    prefix_length = len(prefix)
    try:
        payload = body[prefix_length:].decode(
            "utf-8",
            errors="strict",
        )
        parsed = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _normalize_json_value(
    value: Any,
    *,
    string_normalizer: Callable[[str], Any] | None,
) -> Any:
    """Normalize one JSON-compatible value recursively."""
    if isinstance(value, dict):
        return _normalize_json_mapping(value, string_normalizer=string_normalizer)
    if isinstance(value, list):
        return [
            _normalize_json_value(item, string_normalizer=string_normalizer)
            for item in value
        ]
    if isinstance(value, str):
        return _normalize_json_string(value, string_normalizer=string_normalizer)
    return value


def _normalize_json_mapping(
    value: dict[Any, Any],
    *,
    string_normalizer: Callable[[str], Any] | None,
) -> Any:
    """Normalize one JSON mapping, including inline media payloads."""
    normalized_media = _normalize_inline_media_dict(
        value,
        string_normalizer=string_normalizer,
    )
    if normalized_media is not None:
        return normalized_media
    return {
        key: _normalize_json_value(item, string_normalizer=string_normalizer)
        for key, item in sorted(value.items())
    }


def _normalize_json_string(
    value: str,
    *,
    string_normalizer: Callable[[str], Any] | None,
) -> Any:
    """Normalize one JSON string, including embedded media payloads."""
    normalized_media = _normalize_embedded_media_string(value)
    if normalized_media is not None:
        return normalized_media
    return string_normalizer(value) if string_normalizer is not None else value


def _normalize_inline_media_dict(
    value: dict[str, Any],
    *,
    string_normalizer: Callable[[str], Any] | None,
) -> dict[str, Any] | None:
    """Normalize an inline-media mapping when its payload is valid."""
    data = value.get("data")
    mime_type = value.get("mimeType") or value.get("mime_type")
    if not isinstance(data, str) or not isinstance(mime_type, str):
        return None

    decoded = decode_base64_bytes(data)
    if decoded is None:
        return None

    normalized = {
        key: _normalize_json_value(item, string_normalizer=string_normalizer)
        for key, item in sorted(value.items())
        if key != "data"
    }
    normalized["data"] = normalize_inline_media_bytes(
        mime_type=mime_type,
        data=decoded,
    )
    return normalized


def _normalize_embedded_media_string(value: str) -> dict[str, Any] | None:
    """Normalize a media data URL embedded in a JSON string."""
    data_url = parse_data_url(value)
    if data_url is not None:
        mime_type, decoded = data_url
        return normalize_inline_media_bytes(mime_type=mime_type, data=decoded)
    return None


def _describe_dict_difference(
    left: dict[Any, Any],
    right: dict[Any, Any],
    path: str,
) -> str:
    """Describe the first semantic difference between two mappings."""
    left_keys = set(left)
    right_keys = set(right)
    if left_keys != right_keys:
        missing_left = sorted(right_keys - left_keys)
        missing_right = sorted(left_keys - right_keys)
        return (
            f"{path}: key mismatch; "
            f"missing_left={missing_left}, missing_right={missing_right}"
        )

    for key in sorted(left):
        if left[key] != right[key]:
            child_path = f"{path}.{key}"
            return describe_first_difference(left[key], right[key], child_path)
    return f"{path}: values differ"


def _describe_list_difference(left: list[Any], right: list[Any], path: str) -> str:
    """Describe the first semantic difference between two lists."""
    if len(left) != len(right):
        return f"{path}: length {len(left)} != {len(right)}"

    for index, (left_item, right_item) in enumerate(zip(left, right, strict=True)):
        if left_item != right_item:
            return describe_first_difference(
                left_item,
                right_item,
                f"{path}[{index}]",
            )
    return f"{path}: values differ"


def _summarize_value(value: Any) -> str:
    """Render one value as a bounded diagnostic fragment."""
    if isinstance(value, str):
        return repr(_truncate_text(value))
    return _truncate_text(repr(value))


def _truncate_text(text: str, limit: int = 120) -> str:
    """Truncate diagnostic text while preserving its original length."""
    if len(text) <= limit:
        return text
    return f"{text[:limit]}...<{len(text)} chars>"


def _headers_items(headers: Any) -> Iterable[tuple[Any, Any]]:
    """Return header items from mapping-like request headers."""
    items = getattr(headers, "items", None)
    if callable(items):
        return items()
    return []


def _infer_boundary_from_body(body: bytes) -> bytes | None:
    """Infer a multipart boundary from the first body line."""
    if not body.startswith(b"--"):
        return None
    first_line_end = body.find(b"\r\n")
    if first_line_end == -1:
        return None
    boundary = body[2:first_line_end]
    return boundary or None
