"""Built-in default declarations for py-lib-testkit.

Why:
    Keeps shared tooling defaults in one declarative place instead of
    scattering them across private config assembly.
"""

from __future__ import annotations

# =============================================================================
# Platform Lanes
# =============================================================================

SUPPORTED_LIBRARY_LANES = ("standard-lib",)

# =============================================================================
# Logging Defaults
# =============================================================================

DEFAULT_LOGGING_LOCAL_LEVEL = "DEBUG"
