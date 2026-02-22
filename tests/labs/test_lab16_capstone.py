"""Exercise tests for Lab 16 scenario runner."""

from __future__ import annotations

from pathlib import Path

import pytest

from pycie.model.capabilities import CapabilityMatrix
from pycie.scenario.dsl import Expectation, Scenario, ScenarioAction, TopologySpec
from pycie.scenario.runner import ScenarioRunner

pytestmark = [pytest.mark.exercise, pytest.mark.lab16]


def test_scenario_runner_executes_actions_and_expectations() -> None:
    matrix = CapabilityMatrix.from_json(Path("labs/capabilities.json"))
    runner = ScenarioRunner(capability_matrix=matrix)

    scenario = Scenario(
        name="mini-capstone",
        lab_id="lab16",
        topology=TopologySpec(nodes=("r1", "r2"), links=(("r1:eth0", "r2:eth0"),)),
        actions=[ScenarioAction(at_ms=100, action="fail_link", params={"a": "r1:eth0", "b": "r2:eth0"})],
        expectations=[Expectation(kind="event_seen", selector="fail_link", expected=True)],
    )

    result = runner.run(scenario)
    assert result.passed
    assert result.failures == []
