"""Validate and normalize py-lib-testkit config input."""

from __future__ import annotations

_TOOL_TABLE = "ternforge"
_RUNTIME_TOOL_TABLE = "py_lib_runtime"
_RUNTIME_LOGGING_TABLE = "logging"


def normalize_package_names(value: object) -> tuple[str, ...]:
    """Return normalized package names from a TOML string array."""
    return normalize_string_tuple(value, field_name="package_names")


def optional_runtime_logging_table(tool: dict[str, object]) -> dict[str, object]:
    """Return optional runtime logging policy from `pyproject.toml`."""
    runtime = tool.get(_RUNTIME_TOOL_TABLE)
    if runtime is None:
        return {}
    if not isinstance(runtime, dict):
        msg = f"pyproject.toml [tool.{_RUNTIME_TOOL_TABLE}] must be a table."
        raise TypeError(msg)

    logging_config = runtime.get(_RUNTIME_LOGGING_TABLE)
    if logging_config is None:
        return {}
    if not isinstance(logging_config, dict):
        msg = (
            "pyproject.toml "
            f"[tool.{_RUNTIME_TOOL_TABLE}.{_RUNTIME_LOGGING_TABLE}] must be a table."
        )
        raise TypeError(msg)
    return logging_config


def optional_string(
    table: dict[str, object],
    key: str,
    *,
    default: str,
) -> str:
    """Return an optional non-empty string with a default."""
    value = table.get(key, default)
    if not isinstance(value, str) or not value.strip():
        msg = f"pyproject.toml field {key!r} must be a non-empty string."
        raise ValueError(msg)
    return value.strip()


def optional_string_tuple(
    value: object,
    *,
    field_name: str,
) -> tuple[str, ...] | None:
    """Return optional normalized non-empty strings from a TOML string array."""
    if value is None:
        return None
    return normalize_string_tuple(value, field_name=field_name)


def normalize_string_tuple(value: object, *, field_name: str) -> tuple[str, ...]:
    """Return normalized non-empty strings from a TOML string array."""
    if not isinstance(value, list):
        msg = f"pyproject.toml [tool.{_TOOL_TABLE}].{field_name} must be a list."
        raise TypeError(msg)

    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            msg = (
                f"pyproject.toml [tool.{_TOOL_TABLE}].{field_name} items must be "
                "non-empty strings."
            )
            raise ValueError(msg)
        normalized.append(item.strip())
    return tuple(dict.fromkeys(normalized))


def require_table(
    raw_config: dict[str, object],
    key: str,
    *,
    table_name: str | None = None,
) -> dict[str, object]:
    """Return one required TOML table."""
    value = raw_config.get(key)
    if not isinstance(value, dict):
        msg = f"pyproject.toml must define a [{table_name or key}] table."
        raise TypeError(msg)
    return value


def require_string(table: dict[str, object], key: str) -> str:
    """Return one required non-empty string from a TOML table."""
    value = table.get(key)
    if not isinstance(value, str) or not value.strip():
        msg = f"pyproject.toml field {key!r} must be a non-empty string."
        raise ValueError(msg)
    return value.strip()
