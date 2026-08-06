"""Private shared test-support implementation exports.

Why:
    Provides narrow private entrypoints used by the public test-support facade
    while concrete helpers stay grouped by concern.
"""

from __future__ import annotations

from py_lib_testkit._internal.test_support._vcr_shared import (
    compare_optional_json_bodies as compare_optional_json_bodies,
)
from py_lib_testkit._internal.test_support._vcr_shared import (
    compare_optional_multipart_single_file_content as _compare_multipart_content,
)
from py_lib_testkit._internal.test_support._vcr_shared import (
    decode_base64_bytes as decode_base64_bytes,
)
from py_lib_testkit._internal.test_support._vcr_shared import (
    describe_first_difference as describe_first_difference,
)
from py_lib_testkit._internal.test_support._vcr_shared import (
    extract_boundary as extract_boundary,
)
from py_lib_testkit._internal.test_support._vcr_shared import (
    extract_single_part_content as extract_single_part_content,
)
from py_lib_testkit._internal.test_support._vcr_shared import (
    get_header_value as get_header_value,
)
from py_lib_testkit._internal.test_support._vcr_shared import (
    is_png as is_png,
)
from py_lib_testkit._internal.test_support._vcr_shared import (
    multipart_signature_prefix as multipart_signature_prefix,
)
from py_lib_testkit._internal.test_support._vcr_shared import (
    normalize_inline_media_bytes as normalize_inline_media_bytes,
)
from py_lib_testkit._internal.test_support._vcr_shared import (
    normalize_json_body as normalize_json_body,
)
from py_lib_testkit._internal.test_support._vcr_shared import (
    parse_data_url as parse_data_url,
)
from py_lib_testkit._internal.test_support._vcr_shared import (
    png_pixels_digest as png_pixels_digest,
)
from py_lib_testkit._internal.test_support._vcr_shared import (
    png_pixels_signature as png_pixels_signature,
)
from py_lib_testkit._internal.test_support._vcr_shared import (
    strip_ascii_whitespace as strip_ascii_whitespace,
)
from py_lib_testkit._internal.test_support._vcr_shared import (
    to_bytes as to_bytes,
)
from py_lib_testkit._internal.test_support.console import DemoConsole as DemoConsole
from py_lib_testkit._internal.test_support.e2e_vcr_guard import (
    cassette_file_path as cassette_file_path,
)
from py_lib_testkit._internal.test_support.e2e_vcr_guard import (
    require_vcr_cassette_or_record_mode as require_vcr_cassette_or_record_mode,
)
from py_lib_testkit._internal.test_support.images import (
    image_changed as image_changed,
)
from py_lib_testkit._internal.test_support.images import (
    save_test_output_image as save_test_output_image,
)
from py_lib_testkit._internal.test_support.paths import (
    get_test_data_path as get_test_data_path,
)
from py_lib_testkit._internal.test_support.paths import (
    get_test_output_dir as get_test_output_dir,
)
from py_lib_testkit._internal.test_support.paths import (
    get_test_output_path as get_test_output_path,
)
from py_lib_testkit._internal.test_support.paths import (
    get_workbench_output_dir as get_workbench_output_dir,
)
from py_lib_testkit._internal.test_support.paths import (
    get_workbench_output_path as get_workbench_output_path,
)
from py_lib_testkit._internal.test_support.setup import (
    configure_direct_module_process as configure_direct_module_process,
)
from py_lib_testkit._internal.test_support.setup import (
    configure_pytest_process as configure_pytest_process,
)
from py_lib_testkit._internal.test_support.setup import (
    run_async as run_async,
)
from py_lib_testkit._internal.test_support.vcr_matchers import (
    json_semantic_body as json_semantic_body,
)
from py_lib_testkit._internal.test_support.vcr_matchers import (
    method_case_insensitive as method_case_insensitive,
)
from py_lib_testkit._internal.test_support.vcr_matchers import (
    multipart_single_file_content as multipart_single_file_content,
)

compare_optional_multipart_single_file_content = _compare_multipart_content
