"""DemoConsole JSON rendering tests.

Why:
    Many repositories use `DemoConsole` for manual workbench scripts executed via
    `python -m ...`. JSON rendering must be stable and must not crash when
    passing options through to `json.dumps`.
"""

from __future__ import annotations

from io import StringIO

from py_lib_testkit import DemoConsole

# =============================================================================
# Tests
# =============================================================================


def test_demo_console_print_renders_dict_as_json() -> None:
    buffer = StringIO()
    console = DemoConsole(
        file=buffer,
        force_terminal=False,
        force_jupyter=False,
        width=80,
    )

    console.print({"b": 2, "a": 1})

    output = buffer.getvalue()
    assert '"a"' in output
    assert '"b"' in output


def test_demo_console_print_json_supports_skip_keys() -> None:
    buffer = StringIO()
    console = DemoConsole(
        file=buffer,
        force_terminal=False,
        force_jupyter=False,
        width=80,
    )

    console.print_json(data={("not", "json"): 1}, skip_keys=True)

    output = buffer.getvalue()
    assert "{" in output
    assert "}" in output
