"""Check public config validation across unknown library lanes."""

from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from py_lib_testkit import ProjectToolingConfig


@given(
    st.text(alphabet=st.characters(categories=("Ll",)), min_size=1, max_size=8).filter(
        lambda value: value != "standard-lib"
    )
)
def test_unknown_library_lanes_fail_closed(library_lane: str) -> None:
    with pytest.raises(ValueError, match="library_lane must be one of"):
        ProjectToolingConfig(
            distribution_name="sample-lib",
            distribution_version="1.2.3",
            primary_package="sample_lib",
            package_names=("sample_lib",),
            env_prefix="SAMPLE_LIB",
            library_lane=library_lane,
        )
