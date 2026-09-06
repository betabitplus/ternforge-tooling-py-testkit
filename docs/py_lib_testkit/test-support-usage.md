---
name: test-support-usage
doc_type: usage
description: Shared test helpers exported by py_lib_testkit.
---

# 1 Test Support

## 1.1 Overview

`test_support` contains shared test utilities exported by `py_lib_testkit`. It is primarily for tests, especially e2e tests that use VCR cassettes.

## 1.2 Features

- Provides standard Pytest process configuration.
- Includes VCR request matchers.
- Standardizes test data/output path resolution.
- Exposes developer productivity helpers for interactive async runs.
- Offers comparison helpers for images, JSON bodies, and multipart requests.
- Publishes typed evidence to IPython and, when installed, Allure.

## 1.3 Examples

### 1.3.1 Configuring Pytest

Use this from `tests/conftest.py` to lower package log noise during pytest runs.

```python
from py_lib_testkit import configure_pytest_process

configure_pytest_process()
```

### 1.3.2 Resolving Standard Paths

Use these to fetch standardized, ignored directories for test inputs and outputs.

```python
from py_lib_testkit import get_test_data_path, get_test_output_path

# Test outputs go under ignored output directories
data_path = get_test_data_path("sample_lib")
output_path = get_test_output_path(
    "output.txt",
    module_name="sample_lib",
)
```

### 1.3.3 Interactive Async Helpers

Use `run_async` when interactive code must also work inside an already-running event loop.

```python
from py_lib_testkit import DemoConsole, run_async

console = DemoConsole()
console.print("Running interactive probe...")
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

### 1.3.6 Publishing Rich Evidence

Use typed evidence for results that should be visible in an IPython run and persisted by an installed Allure adapter. JSON values must already be JSON-serializable; file evidence uses MIME types.

```python
from py_lib_testkit import evidence

evidence.json("Result", result.model_dump(mode="json"))
evidence.file("Generated video", video_path, media_type="video/mp4")
```

## 1.4 Runnable Examples

- [test_support_demo.py](../../examples/py_lib_testkit/test_support_demo.py)
  Run with: `uv run python examples/py_lib_testkit/test_support_demo.py`
