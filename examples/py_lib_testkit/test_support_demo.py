# %%
"""Demonstrate the public test-support console helper."""

from py_lib_testkit import DemoConsole


def main() -> None:
    """Print one styled message through the supported public API."""
    DemoConsole().print("py-lib-testkit is ready")


if __name__ == "__main__":
    main()
