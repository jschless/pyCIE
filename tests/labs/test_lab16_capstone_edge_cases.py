"""Edge-case tests for Lab 16 capstone runner."""

from __future__ import annotations

from pathlib import Path

import pytest

from pycie.model.capabilities import CapabilityMatrix
from pycie.scenario.dsl import Expectation, Scenario, ScenarioAction, TopologySpec
from pycie.scenario.runner import ScenarioRunner

pytestmark = [pytest.mark.exercise, pytest.mark.lab16]


def _matrix() -> CapabilityMatrix:
    return CapabilityMatrix.from_json(Path("labs/capabilities.json"))


def test_runner_executes_actions_in_timestamp_order() -> None:
    runner = ScenarioRunner(capability_matrix=_matrix())
    scenario = Scenario(
        name="ordered-actions",
        lab_id="lab16",
        topology=TopologySpec(nodes=("r1", "r2"), links=(("r1:eth0", "r2:eth0"),)),
        actions=[
            ScenarioAction(at_ms=200, action="fail_link", params={"a": "r1:eth0", "b": "r2:eth0"}),
            ScenarioAction(at_ms=100, action="fail_bgp_peer", params={"node": "r1", "peer": "r2"}),
        ],
        expectations=[],
    )

    result = runner.run(scenario)
    events = result.telemetry["events"]
    assert events[0]["params"]["_at_ms"] == 100
    assert events[1]["params"]["_at_ms"] == 200


def test_runner_reports_expectation_failures() -> None:
    runner = ScenarioRunner(capability_matrix=_matrix())
    scenario = Scenario(
        name="failing-expectation",
        lab_id="lab16",
        topology=TopologySpec(nodes=("r1",), links=()),
        actions=[],
        expectations=[Expectation(kind="event_seen", selector="fail_link", expected=True)],
    )

    result = runner.run(scenario)
    assert not result.passed
    assert result.failures
