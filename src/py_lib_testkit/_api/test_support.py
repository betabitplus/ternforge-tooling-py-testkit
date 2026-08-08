"""Public shared test-support facade for py-lib-testkit.

Why:
    Keeps reusable test/demo helpers on the supported root package boundary
    while private modules own setup, VCR, path, image, and console mechanics.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path

from PIL import Image

from py_lib_testkit._internal import (
    DemoConsole as _DemoConsole,
    cassette_file_path as _cassette_file_path,
    compare_optional_json_bodies as _compare_optional_json_bodies,
    compare_optional_multipart_single_file_content as _compare_multipart_content,
    configure_direct_module_process as _configure_direct_module_process,
    configure_pytest_process as _configure_pytest_process,
    decode_base64_bytes as _decode_base64_bytes,
    describe_first_difference as _describe_first_difference,
    extract_boundary as _extract_boundary,
    extract_single_part_content as _extract_single_part_content,
    get_header_value as _get_header_value,
    get_test_data_path as _get_test_data_path,
    get_test_output_dir as _get_test_output_dir,
    get_test_output_path as _get_test_output_path,
    get_workbench_output_dir as _get_workbench_output_dir,
    get_workbench_output_path as _get_workbench_output_path,
    image_changed as _image_changed,
    is_png as _is_png,
    json_semantic_body as _json_semantic_body,
    method_case_insensitive as _method_case_insensitive,
    multipart_signature_prefix as _multipart_signature_prefix,
    multipart_single_file_content as _multipart_single_file_content,
    normalize_inline_media_bytes as _normalize_inline_media_bytes,
    normalize_json_body as _normalize_json_body,
    parse_data_url as _parse_data_url,
    png_pixels_digest as _png_pixels_digest,
    png_pixels_signature as _png_pixels_signature,
    require_vcr_cassette_or_record_mode as _require_vcr_cassette_or_record_mode,
    run_async as _run_async,
    save_test_output_image as _save_test_output_image,
    strip_ascii_whitespace as _strip_ascii_whitespace,
    to_bytes as _to_bytes,
)

# =============================================================================
# Console Facade
# =============================================================================


class DemoConsole(_DemoConsole):
    """Public rich console facade for manual demos."""


console = DemoConsole(highlight=True)


# =============================================================================
# Setup Facade
# =============================================================================


def run_async[T](awaitable: Awaitable[T]) -> T:
    """Run one coroutine in normal and already-running loop contexts."""
    return _run_async(awaitable)


def configure_pytest_process(*, start: Path | None = None) -> None:
    """Keep the repo's package logs quiet during pytest runs."""
    _configure_pytest_process(start=start)


def configure_direct_module_process(
    *,
    main_file: str | None,
    package_root: Path,
    configure_logging_from_env: str | None = None,
    configure_logging_from_env_suffix: str | None = None,
) -> None:
    """Configure one package for direct `python -m ...` execution."""
    _configure_direct_module_process(
        main_file=main_file,
        package_root=package_root,
        configure_logging_from_env=configure_logging_from_env,
        configure_logging_from_env_suffix=configure_logging_from_env_suffix,
    )


# =============================================================================
# Path Facade
# =============================================================================


def get_test_data_path(module_name: str, *, start: Path | None = None) -> Path:
    """Return the `tests/<module_name>/data` directory."""
    return _get_test_data_path(module_name, start=start)


def get_test_output_dir(
    module_name: str | None = None,
    *,
    start: Path | None = None,
) -> Path:
    """Return the ignored test output directory for a module or repo."""
    return _get_test_output_dir(module_name, start=start)


def get_test_output_path(
    filename: str,
    *,
    module_name: str | None = None,
    start: Path | None = None,
) -> Path:
    """Return an ignored test output file path."""
    return _get_test_output_path(filename, module_name=module_name, start=start)


def get_workbench_output_dir(
    module_name: str | None = None,
    *,
    start: Path | None = None,
) -> Path:
    """Return the ignored workbench output directory for a module or repo."""
    return _get_workbench_output_dir(module_name, start=start)


def get_workbench_output_path(
    filename: str,
    *,
    module_name: str | None = None,
    start: Path | None = None,
) -> Path:
    """Return an ignored workbench output file path."""
    return _get_workbench_output_path(filename, module_name=module_name, start=start)


# =============================================================================
# Image Facade
# =============================================================================


def image_changed(before: Image.Image, after: Image.Image) -> bool:
    """Return whether two images differ after RGB normalization."""
    return _image_changed(before, after)


def save_test_output_image(
    image: Image.Image,
    filename: str,
    *,
    module_name: str | None = None,
) -> Path:
    """Save an image under the ignored test output directory."""
    return _save_test_output_image(image, filename, module_name=module_name)


# =============================================================================
# VCR Guard Facade
# =============================================================================


def cassette_file_path(*, test_file: str, test_name: str) -> Path:
    """Return the canonical cassette file path for an e2e test function."""
    return _cassette_file_path(test_file=test_file, test_name=test_name)


def require_vcr_cassette_or_record_mode(*, test_file: str, test_name: str) -> None:
    """Fail when replay data is missing and no explicit recording mode is active."""
    _require_vcr_cassette_or_record_mode(test_file=test_file, test_name=test_name)


# =============================================================================
# VCR Request Matcher Facade
# =============================================================================


def method_case_insensitive(r1: object, r2: object) -> None:
    """Match HTTP methods case-insensitively."""
    _method_case_insensitive(r1, r2)


def multipart_single_file_content(r1: object, r2: object) -> None:
    """Match multipart single-file uploads by extracted file content."""
    _multipart_single_file_content(r1, r2)


def json_semantic_body(r1: object, r2: object) -> None:
    """Match JSON bodies after shared semantic normalization."""
    _json_semantic_body(r1, r2)


def compare_optional_multipart_single_file_content(
    r1: object,
    r2: object,
) -> bool | None:
    """Compare multipart single-file bodies, if both requests use that shape."""
    return _compare_multipart_content(r1, r2)


def compare_optional_json_bodies(
    r1: object,
    r2: object,
    *,
    string_normalizer: Callable[[str], object] | None = None,
) -> tuple[bool | None, str | None]:
    """Compare JSON request bodies after generic semantic normalization."""
    return _compare_optional_json_bodies(
        r1,
        r2,
        string_normalizer=string_normalizer,
    )


# =============================================================================
# VCR Body Normalization Facade
# =============================================================================


def normalize_json_body(
    body: bytes,
    *,
    string_normalizer: Callable[[str], object] | None = None,
) -> object:
    """Parse and normalize one JSON body payload."""
    return _normalize_json_body(body, string_normalizer=string_normalizer)


def to_bytes(value: object) -> bytes:
    """Convert supported request-body values into bytes."""
    return _to_bytes(value)


def normalize_inline_media_bytes(*, mime_type: str, data: bytes) -> dict[str, object]:
    """Normalize inline media bytes into a stable semantic signature."""
    return _normalize_inline_media_bytes(mime_type=mime_type, data=data)


def parse_data_url(value: str) -> tuple[str, bytes] | None:
    """Parse one base64 data URL into `(mime_type, decoded_bytes)`."""
    return _parse_data_url(value)


def decode_base64_bytes(value: str) -> bytes | None:
    """Decode wrapped or URL-safe base64 text into raw bytes."""
    return _decode_base64_bytes(value)


def strip_ascii_whitespace(value: str) -> str:
    """Remove ASCII whitespace characters from one string."""
    return _strip_ascii_whitespace(value)


def is_png(data: bytes) -> bool:
    """Return whether one byte string starts with the PNG signature."""
    return _is_png(data)


def describe_first_difference(left: object, right: object, path: str = "$") -> str:
    """Describe the first semantic difference between two normalized values."""
    return _describe_first_difference(left, right, path)


# =============================================================================
# Multipart And PNG Facade
# =============================================================================


def multipart_signature_prefix() -> bytes:
    """Return the repo-specific multipart signature prefix used by VCR helpers."""
    return _multipart_signature_prefix()


def get_header_value(request: object, name: str) -> str:
    """Read one request header case-insensitively from a VCR-style request."""
    return _get_header_value(request, name)


def extract_boundary(content_type: str) -> str | None:
    """Extract the multipart boundary from one content-type header."""
    return _extract_boundary(content_type)


def extract_single_part_content(body: bytes, boundary: str) -> bytes | None:
    """Extract the raw file content from one multipart single-file body."""
    return _extract_single_part_content(body, boundary)


def png_pixels_signature(png_bytes: bytes) -> dict[str, object]:
    """Normalize one PNG into a stable pixel-based signature."""
    return _png_pixels_signature(png_bytes)


def png_pixels_digest(png_bytes: bytes) -> tuple[tuple[int, int], str, bytes]:
    """Return the raw RGBA pixel digest tuple for one PNG."""
    return _png_pixels_digest(png_bytes)
