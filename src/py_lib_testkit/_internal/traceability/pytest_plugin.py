"""Pytest transport for requirement traceability metadata.

The plugin intentionally does not know the Ternforge requirements model. It only
normalizes requirement references from pytest/Gherkin into JUnit properties and
rejects orphan tests when a repository opts into traceability enforcement.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

_TRACEABILITY_INI: Final = "ternforge_traceability"
_VERIFIES_MARKER: Final = "verifies"
_KIND_MARKER: Final = "verification_kind"
_REQUIREMENT_TAG_RE: Final = re.compile(r"^(?:REQ|TREQ)_[A-Z0-9_]+(?:\[[^\]]+\])?$")
_VALID_KINDS: Final = frozenset({"bdd", "unit", "property", "integration", "e2e"})


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register traceability configuration without enabling it by default."""
    parser.addini(
        _TRACEABILITY_INI,
        "Require every collected test to declare requirement traceability metadata.",
        type="bool",
        default=False,
    )


def pytest_configure(config: pytest.Config) -> None:
    """Register markers used by the transport layer."""
    config.addinivalue_line(
        "markers",
        "verifies(*requirements): requirement IDs verified by this test",
    )
    config.addinivalue_line(
        "markers",
        (
            "verification_kind(kind): explicit evidence kind for an otherwise "
            "unclassified test"
        ),
    )


@pytest.hookimpl(optionalhook=True, tryfirst=True)
def pytest_bdd_apply_tag(tag: str, function: object) -> bool | None:
    """Translate requirement-shaped Gherkin tags into normal pytest metadata."""
    if not _REQUIREMENT_TAG_RE.fullmatch(tag):
        return None

    pytest.mark.verifies(tag)(function)
    pytest.mark.verification_kind("bdd")(function)
    return True


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Export declared trace metadata and optionally reject orphan tests."""
    require_trace = config.getini(_TRACEABILITY_INI)
    violations = [
        violation
        for item in items
        if (violation := _trace_item(item, require_trace=require_trace)) is not None
    ]
    if violations:
        lines = ["Ternforge traceability collection failed:", *violations]
        raise pytest.UsageError("\n".join(lines))


def _trace_item(item: pytest.Item, *, require_trace: bool) -> str | None:
    """Attach declared trace properties or return one collection violation."""
    requirements = _requirement_refs(item)
    if not requirements:
        if require_trace:
            return f"  - untraced test: {item.nodeid}"
        return None

    kind = _verification_kind(item)
    if kind is None:
        return (
            f"  - invalid trace metadata: {item.nodeid}: verification kind is unknown"
        )

    _set_user_property(item, "verifies", ",".join(requirements))
    _set_user_property(item, "verification_kind", kind)
    return None


@pytest.hookimpl(optionalhook=True)
def pytest_bdd_before_scenario(
    request: pytest.FixtureRequest,
    feature: object,
    scenario: object,
) -> None:
    """Add exact Gherkin source metadata to the current JUnit testcase."""
    node = request.node
    feature_path = getattr(feature, "filename", None)
    scenario_name = getattr(scenario, "name", None)

    if feature_path:
        _set_user_property(
            node,
            "gherkin_feature",
            _relative_path(request.config.rootpath, Path(str(feature_path))),
        )
    if scenario_name:
        _set_user_property(node, "gherkin_scenario", str(scenario_name))


def _requirement_refs(item: pytest.Item) -> tuple[str, ...]:
    """Read unique requirement references from markers in declaration order."""
    refs: list[str] = []
    for marker in item.iter_markers(name=_VERIFIES_MARKER):
        for value in marker.args:
            if not isinstance(value, str) or not value.strip():
                msg = (
                    f"{item.nodeid}: verifies marker arguments must be "
                    "non-empty strings"
                )
                raise pytest.UsageError(msg)
            ref = value.strip()
            if not _REQUIREMENT_TAG_RE.fullmatch(ref):
                msg = f"{item.nodeid}: invalid requirement reference: {ref}"
                raise pytest.UsageError(msg)
            if ref not in refs:
                refs.append(ref)
    return tuple(refs)


def _verification_kind(item: pytest.Item) -> str | None:
    """Resolve one evidence kind while tolerating repeated identical declarations."""
    markers = list(item.iter_markers(name=_KIND_MARKER))
    if not markers:
        return None

    values: list[str] = []
    for marker in markers:
        if len(marker.args) != 1:
            msg = f"{item.nodeid}: verification_kind expects exactly one value"
            raise pytest.UsageError(msg)
        value = marker.args[0]
        if not isinstance(value, str) or value not in _VALID_KINDS:
            allowed = ", ".join(sorted(_VALID_KINDS))
            msg = f"{item.nodeid}: verification_kind must be one of: {allowed}"
            raise pytest.UsageError(msg)
        values.append(value)

    if len(set(values)) != 1:
        msg = f"{item.nodeid}: verification_kind declarations must agree"
        raise pytest.UsageError(msg)
    return values[0]


def _set_user_property(item: pytest.Item, name: str, value: str) -> None:
    """Set one deterministic JUnit user property without duplicate keys."""
    item.user_properties[:] = [
        (existing_name, existing_value)
        for existing_name, existing_value in item.user_properties
        if existing_name != name
    ]
    item.user_properties.append((name, value))


def _relative_path(root: Path, path: Path) -> str:
    """Render a source path relative to the pytest root when possible."""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()
