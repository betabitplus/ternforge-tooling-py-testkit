"""Tests for the pytest traceability transport plugin."""

from __future__ import annotations

from pathlib import Path

import pytest
from defusedxml import ElementTree

pytest_plugins = ("pytester",)


def _enable_plugin(pytester: pytest.Pytester) -> None:
    pytester.makeini(
        """
        [pytest]
        ternforge_traceability = true
        addopts = --strict-markers
        """
    )


def _properties(report: Path, testcase_name: str) -> dict[str, str]:
    root = ElementTree.parse(report).getroot()
    testcase = next(
        item for item in root.iter("testcase") if item.attrib["name"] == testcase_name
    )
    properties = testcase.find("properties")
    assert properties is not None
    return {
        item.attrib["name"]: item.attrib["value"]
        for item in properties.findall("property")
    }


def test_orphan_test_fails_collection(pytester: pytest.Pytester) -> None:
    _enable_plugin(pytester)
    pytester.makepyfile(
        """
        def test_orphan():
            assert True
        """
    )

    result = pytester.runpytest()

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(["*untraced test:*test_orphan*"])


def test_traced_test_exports_requirement_and_kind(pytester: pytest.Pytester) -> None:
    _enable_plugin(pytester)
    pytester.makepyfile(
        """
import pytest

@pytest.mark.verifies("TREQ_ROUTE_ORDER[revision==2]")
@pytest.mark.verification_kind("unit")
def test_route_order():
    assert True
"""
    )
    report = pytester.path / "report.xml"

    result = pytester.runpytest(f"--junitxml={report}")

    result.assert_outcomes(passed=1)
    assert _properties(report, "test_route_order") == {
        "verification_kind": "unit",
        "verifies": "TREQ_ROUTE_ORDER[revision==2]",
    }


def test_non_bdd_test_requires_explicit_kind_even_in_named_directory(
    pytester: pytest.Pytester,
) -> None:
    _enable_plugin(pytester)
    unit_dir = pytester.path / "tests" / "sample" / "unit"
    unit_dir.mkdir(parents=True)
    unit_dir.joinpath("test_route.py").write_text(
        """
import pytest

@pytest.mark.verifies("REQ_PUBLIC_CONTRACT")
def test_public_contract():
    assert True
""",
        encoding="utf-8",
    )

    result = pytester.runpytest(str(unit_dir))

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(
        ["*invalid trace metadata:*verification kind is unknown*"]
    )


def test_gherkin_requirement_tag_exports_bdd_source_metadata(
    pytester: pytest.Pytester,
) -> None:
    _enable_plugin(pytester)
    feature = pytester.path / "features" / "fallback.feature"
    feature.parent.mkdir()
    feature.write_text(
        """@REQ_ROUTE_FALLBACK[revision==3]
Feature: Route fallback

  Scenario: Failed route falls back
    Given the route can fall back
    When the preferred route fails
    Then the fallback route is used
""",
        encoding="utf-8",
    )
    pytester.makepyfile(
        test_scenarios="""
from pytest_bdd import given, scenarios, then, when

scenarios("features")

@given("the route can fall back")
def route_can_fall_back():
    return None

@when("the preferred route fails")
def preferred_route_fails():
    return None

@then("the fallback route is used")
def fallback_route_is_used():
    return None
"""
    )
    report = pytester.path / "report.xml"

    result = pytester.runpytest(f"--junitxml={report}")

    result.assert_outcomes(passed=1)
    properties = _properties(report, "test_failed_route_falls_back")
    assert properties["verifies"] == "REQ_ROUTE_FALLBACK[revision==3]"
    assert properties["verification_kind"] == "bdd"
    assert properties["gherkin_feature"] == "features/fallback.feature"
    assert properties["gherkin_scenario"] == "Failed route falls back"


def test_multiple_requirement_links_survive_skip(pytester: pytest.Pytester) -> None:
    _enable_plugin(pytester)
    pytester.makepyfile(
        """
import pytest

@pytest.mark.verifies("REQ_ROUTE", "TREQ_ROUTE_ORDER[revision==4]")
@pytest.mark.verification_kind("integration")
@pytest.mark.skip(reason="synthetic skip")
def test_skipped_trace():
    assert True
"""
    )
    report = pytester.path / "report.xml"

    result = pytester.runpytest(f"--junitxml={report}")

    result.assert_outcomes(skipped=1)
    assert _properties(report, "test_skipped_trace") == {
        "verification_kind": "integration",
        "verifies": "REQ_ROUTE,TREQ_ROUTE_ORDER[revision==4]",
    }


def test_trace_metadata_survives_xdist(pytester: pytest.Pytester) -> None:
    _enable_plugin(pytester)
    pytester.makepyfile(
        """
import pytest

@pytest.mark.verifies("TREQ_PARALLEL")
@pytest.mark.verification_kind("unit")
def test_parallel_trace():
    assert True
"""
    )
    report = pytester.path / "report.xml"

    result = pytester.runpytest_subprocess("-n", "2", f"--junitxml={report}")

    result.assert_outcomes(passed=1)
    assert _properties(report, "test_parallel_trace") == {
        "verification_kind": "unit",
        "verifies": "TREQ_PARALLEL",
    }


def test_trace_metadata_survives_xfail(pytester: pytest.Pytester) -> None:
    _enable_plugin(pytester)
    pytester.makepyfile(
        """
import pytest

@pytest.mark.verifies("REQ_EXPECTED_FAILURE")
@pytest.mark.verification_kind("integration")
@pytest.mark.xfail(reason="synthetic expected failure", strict=True)
def test_expected_failure():
    assert False
"""
    )
    report = pytester.path / "report.xml"
    result = pytester.runpytest(f"--junitxml={report}")
    result.assert_outcomes(xfailed=1)
    assert _properties(report, "test_expected_failure") == {
        "verification_kind": "integration",
        "verifies": "REQ_EXPECTED_FAILURE",
    }


def test_malformed_requirement_reference_fails_collection(
    pytester: pytest.Pytester,
) -> None:
    _enable_plugin(pytester)
    pytester.makepyfile(
        """
import pytest

@pytest.mark.verifies("ROUTE_FALLBACK")
@pytest.mark.verification_kind("integration")
def test_bad_reference():
    assert True
"""
    )

    result = pytester.runpytest()

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(["*invalid requirement reference: ROUTE_FALLBACK*"])


def test_plugin_is_inert_until_traceability_is_enabled(
    pytester: pytest.Pytester,
) -> None:
    pytester.makepyfile(
        """
def test_untraced_legacy_suite():
    assert True
"""
    )

    result = pytester.runpytest()

    result.assert_outcomes(passed=1)
