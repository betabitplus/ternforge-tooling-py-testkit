# System

`_api/config.py` exposes typed project config, `_api/test_support.py` exposes reusable helpers, and `_internal` owns their implementation. The root package remains the only supported consumer import boundary.
