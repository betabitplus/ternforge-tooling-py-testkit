---
name: test-support-usage
doc_type: usage
description: Shared test helpers exported by py_lib_testkit.
---

# 1 Test Support

## 1.1 Overview

`test_support` contains shared test and workbench utilities exported by `py_lib_testkit`. It is primarily for tests, especially e2e tests that use VCR cassettes.

## 1.2 Features

- Provides standard Pytest process configuration.
- Includes robust VCR cassette enforcement and request matchers.
- Standardizes test and workbench data/output path resolution.
- Exposes developer productivity helpers for workbench and interactive runs.
- Offers comparison helpers for images, JSON bodies, and multipart requests.

## 1.3 Examples

### 1.3.1 Configuring Pytest

Use this from `tests/conftest.py` to lower package log noise during pytest runs.

```python
from py_lib_testkit import configure_pytest_process

configure_pytest_process()
```

### 1.3.2 Enforcing E2E VCR Cassettes

Use this when a test should safely replay a committed cassette or fail if recording was not explicitly requested. It accepts pytest `--record-mode=...` or the repo's record-VCR env var.

```python
from py_lib_testkit import require_vcr_cassette_or_record_mode

require_vcr_cassette_or_record_mode(
    test_file=__file__,
    test_name="test_pipeline",
)
```

### 1.3.3 Resolving Standard Paths

Use these to fetch standardized, ignored directories for test inputs and outputs.

```python
from py_lib_testkit import (
    get_test_data_path,
    get_test_output_path,
    get_workbench_output_path,
)

# Test outputs go under ignored output directories
data_path = get_test_data_path("sample_lib")
output_path = get_test_output_path(
    "output.txt",
    module_name="sample_lib",
)

# Workbench outputs go under workbench/.outputs
wb_path = get_workbench_output_path(
    "demo.json",
    module_name="my_demo",
)
```

### 1.3.4 Workbench and Demo Scripts

Use these for direct module execution and async code that must also work in an already-running event loop.

```python
from pathlib import Path

from py_lib_testkit import (
    DemoConsole,
    configure_direct_module_process,
    run_async,
)

configure_direct_module_process(
    main_file=__file__,
    package_root=Path(__file__).resolve().parents[3],
)

console = DemoConsole()
console.print("Running demo...")
```

### 1.3.5 Validating HTTP Requests and Images

Use these in tests that compare images, JSON bodies, or complex multipart requests.

```python
from py_lib_testkit import (
    image_changed,
    json_semantic_body,
    method_case_insensitive,
    multipart_single_file_content,
    normalize_json_body,
)

# Example image comparison check
# assert not image_changed(path_a, path_b)
```

## 1.4 Runnable Examples

- [test_support_demo.py](../../examples/py_lib_testkit/test_support_demo.py)
  Run with: `uv run python packages/py-lib-testkit/examples/py_lib_testkit/test_support_demo.py`
