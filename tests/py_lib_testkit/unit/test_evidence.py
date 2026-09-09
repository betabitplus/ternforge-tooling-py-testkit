from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from py_lib_testkit import evidence
from py_lib_testkit._internal.test_support import evidence as implementation


class _FakeAttach:
    def __init__(self) -> None:
        self.values: list[dict[str, object]] = []
        self.files: list[dict[str, object]] = []

    def __call__(
        self,
        body: str,
        *,
        name: str,
        attachment_type: str,
        extension: str | None,
    ) -> None:
        self.values.append(
            {
                "body": body,
                "name": name,
                "attachment_type": attachment_type,
                "extension": extension,
            }
        )

    def file(
        self,
        source: str,
        *,
        name: str,
        attachment_type: str,
        extension: str | None,
    ) -> None:
        self.files.append(
            {
                "source": source,
                "name": name,
                "attachment_type": attachment_type,
                "extension": extension,
            }
        )


class _FakeAllure:
    def __init__(self) -> None:
        self.attach = _FakeAttach()


def _disable_ipython(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(implementation, "get_ipython", lambda: None)


def test_json_publishes_allure_attachment(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeAllure()
    _disable_ipython(monkeypatch)
    monkeypatch.setattr(implementation, "_load_allure", lambda: fake)

    evidence.json("Result", {"answer": 42})

    assert fake.attach.values == [
        {
            "body": '{\n  "answer": 42\n}',
            "name": "Result",
            "attachment_type": "application/json",
            "extension": "json",
        }
    ]


def test_json_requires_explicitly_serializable_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _disable_ipython(monkeypatch)
    monkeypatch.setattr(implementation, "_load_allure", lambda: None)

    with pytest.raises(TypeError):
        evidence.json("Result", {"value": object()})


class _FakeSchema:
    """Small Pydantic-shaped schema provider for contract evidence tests."""

    @classmethod
    def model_json_schema(cls) -> dict[str, object]:
        return {
            "title": cls.__name__,
            "type": "object",
            "properties": {"answer": {"type": "integer"}},
        }


def _sample_tool(*, a: int, b: int) -> int:
    """Add two integers."""
    return a + b


def test_contract_publishes_live_schema_and_callable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeAllure()
    _disable_ipython(monkeypatch)
    monkeypatch.setattr(implementation, "_load_allure", lambda: fake)

    evidence.contract("Response schema", _FakeSchema)
    evidence.contract("Tool · add", _sample_tool)

    assert len(fake.attach.values) == 2
    schema_attachment, callable_attachment = fake.attach.values
    assert (
        schema_attachment["attachment_type"]
        == "application/vnd.ternforge.contract+json"
    )
    schema = json.loads(str(schema_attachment["body"]))
    assert schema["kind"] == "schema"
    assert schema["schema"]["properties"]["answer"] == {"type": "integer"}
    assert schema["qualified_name"].endswith("._FakeSchema")
    callable_payload = json.loads(str(callable_attachment["body"]))
    assert callable_payload["kind"] == "callable"
    assert callable_payload["signature"] == "(*, a: 'int', b: 'int') -> 'int'"
    assert callable_payload["description"] == "Add two integers."


def test_contract_rejects_unsupported_values(monkeypatch: pytest.MonkeyPatch) -> None:
    _disable_ipython(monkeypatch)
    monkeypatch.setattr(implementation, "_load_allure", lambda: None)

    with pytest.raises(TypeError, match="Contract evidence requires"):
        evidence.contract("Unsupported", object())


def test_file_infers_mime_type_and_attaches(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeAllure()
    _disable_ipython(monkeypatch)
    monkeypatch.setattr(implementation, "_load_allure", lambda: fake)
    source = tmp_path / "result.json"
    source.write_text('{"ok": true}', encoding="utf-8")

    evidence.file("Result", source)

    assert fake.attach.files == [
        {
            "source": str(source),
            "name": "Result",
            "attachment_type": "application/json",
            "extension": "json",
        }
    ]


def test_file_rejects_missing_path(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        evidence.file("Missing", tmp_path / "missing.png")


def test_visual_diff_uses_allure_standard_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeAllure()
    _disable_ipython(monkeypatch)
    monkeypatch.setattr(implementation, "_load_allure", lambda: fake)
    paths = []
    for name in ("expected.png", "actual.png", "diff.png"):
        path = tmp_path / name
        Image.new("RGB", (2, 2)).save(path)
        paths.append(path)

    evidence.visual_diff(
        "Comparison",
        expected=paths[0],
        actual=paths[1],
        diff=paths[2],
    )

    attachment = fake.attach.values[0]
    assert attachment["name"] == "Comparison"
    assert attachment["attachment_type"] == "application/vnd.allure.image.diff"
    payload = json.loads(str(attachment["body"]))
    assert set(payload) == {"expected", "actual", "diff"}
    assert all(value.startswith("data:image/png;base64,") for value in payload.values())
