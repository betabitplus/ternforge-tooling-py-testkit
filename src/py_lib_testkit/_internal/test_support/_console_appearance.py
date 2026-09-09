"""Private Rich theme settings for manual demo console output."""

from __future__ import annotations

from dataclasses import dataclass

from rich.theme import Theme


@dataclass(frozen=True, slots=True)
class DemoConsoleAppearance:
    """Visual defaults expressed through Rich's native theme API."""

    theme: Theme


DEFAULT_DEMO_CONSOLE_APPEARANCE = DemoConsoleAppearance(
    theme=Theme(
        {
            "header": "bold cyan",
            "subheader": "bold",
            "info": "dim",
            "success": "bold green",
            "error": "bold red",
            "warning": "yellow",
            "key": "cyan",
            "value": "white",
            "url": "blue underline",
            "progress": "magenta",
        }
    )
)
