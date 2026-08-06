from __future__ import annotations

import asyncio
from pathlib import Path

from PIL import Image

from py_lib_testkit import (
    DemoConsole,
    cassette_file_path,
    get_test_output_path,
    image_changed,
    normalize_json_body,
    run_async,
)


def test_vcr_json_normalization() -> None:
    assert normalize_json_body(b'{"b": 2, "a": 1}') == {"a": 1, "b": 2}


def test_console_helper_renders() -> None:
    console = DemoConsole()
    console.print("testkit")


def test_image_helper_detects_change() -> None:
    before = Image.new("RGB", (1, 1), "black")
    after = Image.new("RGB", (1, 1), "white")
    assert image_changed(before, after)


def test_path_and_fixture_helper() -> None:
    path = get_test_output_path("artifact.txt", module_name="sample")
    assert path.parts[-3:] == (".outputs", "sample", "artifact.txt")


def test_e2e_cassette_path() -> None:
    path = cassette_file_path(test_file=__file__, test_name="test_case")
    assert path.name.endswith(".yaml")


def test_async_setup_helper() -> None:
    async def answer() -> int:
        await asyncio.sleep(0)
        return 42

    assert run_async(answer()) == 42


def test_public_package_has_no_policy_dependency() -> None:
    pyproject = Path(__file__).parents[1] / "pyproject.toml"
    assert "py-lib-policy" not in pyproject.read_text(encoding="utf-8")
