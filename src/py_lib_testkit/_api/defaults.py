"""Built-in default declarations for py-lib-testkit.

Why:
    Keeps shared tooling defaults in one declarative place instead of
    scattering them across private config assembly.
"""

from __future__ import annotations

# =============================================================================
# Platform Lane Defaults
# =============================================================================

DEFAULT_LIBRARY_LANE = "standard-lib"
SUPPORTED_LIBRARY_LANES = (DEFAULT_LIBRARY_LANE,)

# =============================================================================
# Logging Defaults
# =============================================================================

DEFAULT_LOGGING_LOCAL_LEVEL = "DEBUG"
