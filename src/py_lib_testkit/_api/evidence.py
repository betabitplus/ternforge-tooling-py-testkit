"""Public rich-evidence facade for executable specifications and tests."""

from __future__ import annotations

from pathlib import Path

from py_lib_testkit._internal import (
    publish_contract as _publish_contract,
    publish_file as _publish_file,
    publish_json as _publish_json,
    publish_verification_observation as _publish_verification_observation,
    publish_visual_diff as _publish_visual_diff,
)


def json(name: str, payload: object) -> None:
    """Show and persist one explicitly JSON-serializable evidence value."""
    _publish_json(name, payload)


def observation(
    name: str,
    *,
    kind: str,
    payload: object,
) -> None:
    """Persist one structured raw verification observation for downstream analysis."""
    _publish_verification_observation(name, kind=kind, payload=payload)


def boundary_interaction(
    *,
    boundary: str,
    interaction: str,
    participant: str,
    target: str,
    transport: str = "",
) -> None:
    """Persist one objective interaction observed at a verification boundary."""
    values = {
        "boundary": boundary.strip(),
        "interaction": interaction.strip(),
        "participant": participant.strip(),
        "target": target.strip(),
    }
    missing = tuple(key for key, value in values.items() if not value)
    if missing:
        names = ", ".join(missing)
        msg = f"Boundary interaction requires non-empty values for: {names}"
        raise ValueError(msg)
    _publish_verification_observation(
        f"{values['boundary']} boundary interaction",
        kind="boundary-interaction",
        payload={**values, "transport": transport.strip()},
    )


def contract(name: str, value: object) -> None:
    """Show and persist a contract derived from the live schema class or callable."""
    _publish_contract(name, value)


def file(
    name: str,
    path: str | Path,
    *,
    media_type: str | None = None,
) -> None:
    """Show and persist one file using its explicit or inferred MIME type."""
    _publish_file(name, path, media_type=media_type)


def visual_diff(
    name: str,
    *,
    expected: str | Path,
    actual: str | Path,
    diff: str | Path,
) -> None:
    """Show and persist an Allure Expected/Actual/Diff image comparison."""
    _publish_visual_diff(
        name,
        expected=expected,
        actual=actual,
        diff=diff,
    )
