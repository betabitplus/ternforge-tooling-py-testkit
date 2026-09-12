"""Tests for the pytest traceability transport plugin."""

from __future__ import annotations

import json
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
        markers =
            hermetic: runs fully offline
            vcr: uses recorded HTTP replay
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

    result = pytester.runpytest(
        "-p",
        "no:allure_pytest",
        f"--junitxml={report}",
    )

    result.assert_outcomes(passed=1)
    assert _properties(report, "test_route_order") == {
        "verification_kind": "unit",
        "verifies": "TREQ_ROUTE_ORDER[revision==2]",
    }


def test_traced_test_exports_allure_labels_when_plugin_is_active(
    pytester: pytest.Pytester,
) -> None:
    _enable_plugin(pytester)
    pytester.makepyfile(
        """
import pytest

@pytest.mark.verifies(
    "REQ_ROUTE_FALLBACK[revision==3]",
    "TREQ_ROUTE_ORDER[revision==2]",
)
@pytest.mark.verification_kind("integration")
def test_route_order():
    assert True
"""
    )
    report = pytester.path / "report.xml"
    allure_results = pytester.path / "allure-results"

    result = pytester.runpytest_subprocess(
        f"--junitxml={report}",
        f"--alluredir={allure_results}",
    )

    result.assert_outcomes(passed=1)
    assert _properties(report, "test_route_order") == {
        "verification_kind": "integration",
        "verifies": ("REQ_ROUTE_FALLBACK[revision==3],TREQ_ROUTE_ORDER[revision==2]"),
    }
    result_file = next(allure_results.glob("*-result.json"))
    payload = json.loads(result_file.read_text(encoding="utf-8"))
    labels = {(str(label["name"]), str(label["value"])) for label in payload["labels"]}
    assert ("layer", "integration") in labels
    assert ("requirement", "REQ_ROUTE_FALLBACK") in labels
    assert ("requirement", "TREQ_ROUTE_ORDER") in labels


def test_traced_test_exports_structured_execution_observation(
    pytester: pytest.Pytester,
) -> None:
    _enable_plugin(pytester)
    pytester.makepyfile(
        """
import pytest

@pytest.fixture
def sample_fixture():
    return object()

@pytest.mark.verifies("REQ_EXECUTION_CONTEXT[revision==1]")
@pytest.mark.verification_kind("integration")
@pytest.mark.hermetic
def test_execution_context(sample_fixture):
    assert sample_fixture is not None
"""
    )
    allure_results = pytester.path / "allure-results"

    result = pytester.runpytest_subprocess(f"--alluredir={allure_results}")

    result.assert_outcomes(passed=1)
    result_file = next(allure_results.glob("*-result.json"))
    result_payload = json.loads(result_file.read_text(encoding="utf-8"))
    attachment = next(
        item
        for item in result_payload.get("attachments", [])
        if item.get("type") == "application/vnd.ternforge.verification-observation+json"
    )
    source = allure_results / str(attachment["source"])
    observation = json.loads(source.read_text(encoding="utf-8"))
    assert observation["schema_version"] == 1
    assert observation["kind"] == "test-execution"
    payload = observation["payload"]
    assert payload["verification_kind"] == "integration"
    assert payload["path"].endswith(
        "test_traced_test_exports_structured_execution_observation.py"
    )
    assert "sample_fixture" in payload["fixtures"]
    assert payload["markers"] == ["hermetic"]
    assert payload["producer_ids"] == [
        "PRODUCER_PYTEST",
        "PRODUCER_PY_TESTKIT",
        "PRODUCER_ALLURE",
    ]


def test_property_execution_captures_public_hypothesis_marker(
    pytester: pytest.Pytester,
) -> None:
    """Hypothesis execution is captured through its documented pytest marker."""
    _enable_plugin(pytester)
    pytester.makepyfile(
        """
import pytest
from hypothesis import given, strategies as st

@pytest.mark.verifies("REQ_PROPERTY_EXECUTION[revision==1]")
@pytest.mark.verification_kind("property")
@given(value=st.integers(min_value=0, max_value=10))
def test_property_execution(value):
    assert 0 <= value <= 10
"""
    )
    allure_results = pytester.path / "allure-results"

    result = pytester.runpytest_subprocess(f"--alluredir={allure_results}")

    result.assert_outcomes(passed=1)
    result_file = next(allure_results.glob("*-result.json"))
    result_payload = json.loads(result_file.read_text(encoding="utf-8"))
    attachment = next(
        item
        for item in result_payload.get("attachments", [])
        if item.get("type") == "application/vnd.ternforge.verification-observation+json"
    )
    source = allure_results / str(attachment["source"])
    observation = json.loads(source.read_text(encoding="utf-8"))

    assert observation["kind"] == "test-execution"
    assert observation["payload"]["verification_kind"] == "property"
    assert observation["payload"]["markers"] == ["hypothesis"]
    assert observation["payload"]["producer_ids"] == [
        "PRODUCER_PYTEST",
        "PRODUCER_PY_TESTKIT",
        "PRODUCER_ALLURE",
        "PRODUCER_HYPOTHESIS",
    ]


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


def test_bdd_steps_export_exact_binding_source_as_allure_evidence(
    pytester: pytest.Pytester,
) -> None:
    _enable_plugin(pytester)
    feature = pytester.path / "features" / "usage.feature"
    feature.parent.mkdir()
    feature.write_text(
        (
            "@REQ_PUBLIC_USAGE\n"
            "Feature: Public usage\n\n"
            "  Scenario: Execute through the public API\n"
            "    Given a public router\n"
            "    When the client calls query\n"
            "    Then a response is returned\n"
        ),
        encoding="utf-8",
    )
    pytester.makeconftest(
        """
import allure

_steps = {}

def pytest_bdd_before_step(request, step):
    context = allure.step(f"{step.keyword} {step.name}")
    context.__enter__()
    _steps[request.node.nodeid] = context

def pytest_bdd_after_step(request):
    _steps.pop(request.node.nodeid).__exit__(None, None, None)
"""
    )
    pytester.makepyfile(
        test_scenarios="""
from pytest_bdd import given, scenarios, then, when

scenarios("features")

@given("a public router", target_fixture="public_router")
def public_router():
    return object()

@when("the client calls query")
def call_query(public_router):
    return public_router

@then("a response is returned")
def response_is_returned():
    assert True
"""
    )
    allure_results = pytester.path / "allure-results"

    result = pytester.runpytest_subprocess(f"--alluredir={allure_results}")

    result.assert_outcomes(passed=1)
    result_file = next(allure_results.glob("*-result.json"))
    payload = json.loads(result_file.read_text(encoding="utf-8"))
    steps = payload["steps"]
    assert len(steps) == 3
    for step in steps:
        implementations = [
            attachment
            for attachment in step.get("attachments", [])
            if attachment.get("type")
            == "application/vnd.ternforge.bdd-implementation+json"
        ]
        assert len(implementations) == 1
        attachment = implementations[0]
        assert attachment["name"] == "Ternforge BDD implementation"
        source = allure_results / attachment["source"]
        implementation = json.loads(source.read_text(encoding="utf-8"))
        assert implementation["schema_version"] == 1
        assert implementation["path"] == "test_scenarios.py"
        assert implementation["start_line"] <= implementation["end_line"]
        assert implementation["source"].startswith("@")
        assert "def " in implementation["source"]
        assert "public_router" not in implementation.get("arguments", {})


def test_multiple_gherkin_requirement_tags_share_one_bdd_kind(
    pytester: pytest.Pytester,
) -> None:
    _enable_plugin(pytester)
    feature = pytester.path / "features" / "session.feature"
    feature.parent.mkdir()
    feature.write_text(
        """@REQ_SESSION_LIFECYCLE[revision==1]
Feature: Session lifecycle

  @REQ_SESSION_PERSISTENCE[revision==1]
  Scenario: Save and load
    Given a session can be persisted
    When it is loaded
    Then its state is preserved
""",
        encoding="utf-8",
    )
    pytester.makepyfile(
        test_scenarios="""
from pytest_bdd import given, scenarios, then, when

scenarios("features")

@given("a session can be persisted")
def session_can_be_persisted():
    return None

@when("it is loaded")
def session_is_loaded():
    return None

@then("its state is preserved")
def session_state_is_preserved():
    return None
"""
    )
    report = pytester.path / "report.xml"

    result = pytester.runpytest_subprocess("-n", "2", f"--junitxml={report}")

    result.assert_outcomes(passed=1)
    properties = _properties(report, "test_save_and_load")
    assert set(properties["verifies"].split(",")) == {
        "REQ_SESSION_LIFECYCLE[revision==1]",
        "REQ_SESSION_PERSISTENCE[revision==1]",
    }
    assert properties["verification_kind"] == "bdd"


def test_conflicting_verification_kinds_fail_collection(
    pytester: pytest.Pytester,
) -> None:
    _enable_plugin(pytester)
    pytester.makepyfile(
        """
import pytest

@pytest.mark.verifies("REQ_CONFLICT")
@pytest.mark.verification_kind("unit")
@pytest.mark.verification_kind("integration")
def test_conflicting_kind():
    assert True
"""
    )

    result = pytester.runpytest()

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(["*verification_kind declarations must agree*"])


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


def test_untraced_test_remains_allowed_until_orphan_enforcement_is_enabled(
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


def test_declared_trace_exports_before_orphan_enforcement_is_enabled(
    pytester: pytest.Pytester,
) -> None:
    pytester.makepyfile(
        """
import pytest

@pytest.mark.verifies("REQ_INCREMENTAL_ROLLOUT")
@pytest.mark.verification_kind("integration")
def test_traced_pilot():
    assert True

def test_untraced_legacy_suite():
    assert True
"""
    )
    report = pytester.path / "report.xml"

    result = pytester.runpytest(f"--junitxml={report}")

    result.assert_outcomes(passed=2)
    assert _properties(report, "test_traced_pilot") == {
        "verification_kind": "integration",
        "verifies": "REQ_INCREMENTAL_ROLLOUT",
    }
