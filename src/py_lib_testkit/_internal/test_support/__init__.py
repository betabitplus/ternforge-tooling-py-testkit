"""Private shared test-support implementation exports.

Why:
    Provides narrow private entrypoints used by the public test-support facade
    while concrete helpers stay grouped by concern.
"""

from __future__ import annotations

from py_lib_testkit._internal.test_support._vcr_shared import (
    compare_optional_json_bodies as compare_optional_json_bodies,
    compare_optional_multipart_single_file_content as _compare_multipart_content,
    decode_base64_bytes as decode_base64_bytes,
    describe_first_difference as describe_first_difference,
    extract_boundary as extract_boundary,
    extract_single_part_content as extract_single_part_content,
    get_header_value as get_header_value,
    is_png as is_png,
    multipart_signature_prefix as multipart_signature_prefix,
    normalize_inline_media_bytes as normalize_inline_media_bytes,
    normalize_json_body as normalize_json_body,
    parse_data_url as parse_data_url,
    png_pixels_digest as png_pixels_digest,
    png_pixels_signature as png_pixels_signature,
    strip_ascii_whitespace as strip_ascii_whitespace,
    to_bytes as to_bytes,
)
from py_lib_testkit._internal.test_support.console import DemoConsole as DemoConsole
from py_lib_testkit._internal.test_support.evidence import (
    publish_file as publish_file,
    publish_json as publish_json,
    publish_visual_diff as publish_visual_diff,
)
from py_lib_testkit._internal.test_support.images import (
    image_changed as image_changed,
    save_test_output_image as save_test_output_image,
)
from py_lib_testkit._internal.test_support.paths import (
    cassette_file_path as cassette_file_path,
    get_test_data_path as get_test_data_path,
    get_test_output_dir as get_test_output_dir,
    get_test_output_path as get_test_output_path,
)
from py_lib_testkit._internal.test_support.setup import (
    configure_pytest_process as configure_pytest_process,
    run_async as run_async,
)
from py_lib_testkit._internal.test_support.vcr_matchers import (
    json_semantic_body as json_semantic_body,
    method_case_insensitive as method_case_insensitive,
    multipart_single_file_content as multipart_single_file_content,
)

compare_optional_multipart_single_file_content = _compare_multipart_content
