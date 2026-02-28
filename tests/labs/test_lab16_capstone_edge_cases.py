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


def test_runner_convergence_expectation_fails_when_unconverged() -> None:
    runner = ScenarioRunner(capability_matrix=_matrix())
    scenario = Scenario(
        name="unconverged",
        lab_id="lab16",
        topology=TopologySpec(nodes=("r1", "r2"), links=(("r1:eth0", "r2:eth0"),)),
        actions=[ScenarioAction(at_ms=100, action="fail_link", params={"a": "r1:eth0", "b": "r2:eth0"})],
        expectations=[Expectation(kind="convergence_ms_lte", selector="fabric", expected=500)],
    )

    result = runner.run(scenario)
    assert not result.passed
    assert any("actual=unconverged" in failure for failure in result.failures)


def test_runner_rejects_fail_link_for_unknown_topology_link() -> None:
    runner = ScenarioRunner(capability_matrix=_matrix())
    scenario = Scenario(
        name="unknown-link",
        lab_id="lab16",
        topology=TopologySpec(nodes=("r1", "r2"), links=(("r1:eth0", "r2:eth0"),)),
        actions=[ScenarioAction(at_ms=100, action="fail_link", params={"a": "r1:eth9", "b": "r2:eth9"})],
        expectations=[],
    )

    with pytest.raises(ValueError, match="unknown endpoint"):
        runner.run(scenario)


def test_runner_rejects_fail_bgp_peer_for_unknown_node() -> None:
    runner = ScenarioRunner(capability_matrix=_matrix())
    scenario = Scenario(
        name="unknown-bgp-peer",
        lab_id="lab16",
        topology=TopologySpec(nodes=("r1", "r2"), links=(("r1:eth0", "r2:eth0"),)),
        actions=[ScenarioAction(at_ms=100, action="fail_bgp_peer", params={"node": "r1", "peer": "r9"})],
        expectations=[],
    )

    with pytest.raises(ValueError, match="unknown node"):
        runner.run(scenario)


def test_runner_recover_actions_restore_failed_state() -> None:
    runner = ScenarioRunner(capability_matrix=_matrix())
    scenario = Scenario(
        name="recover-actions",
        lab_id="lab16",
        topology=TopologySpec(nodes=("r1", "r2"), links=(("r1:eth0", "r2:eth0"),)),
        actions=[
            ScenarioAction(at_ms=100, action="fail_link", params={"a": "r1:eth0", "b": "r2:eth0"}),
            ScenarioAction(at_ms=110, action="recover_link", params={"a": "r1:eth0", "b": "r2:eth0"}),
            ScenarioAction(at_ms=120, action="fail_bgp_peer", params={"node": "r1", "peer": "r2"}),
            ScenarioAction(at_ms=130, action="recover_bgp_peer", params={"node": "r1", "peer": "r2"}),
        ],
        expectations=[
            Expectation(kind="event_seen", selector="recover_link", expected=True),
            Expectation(kind="event_seen", selector="recover_bgp_peer", expected=True),
        ],
    )

    result = runner.run(scenario)
    assert result.passed
    assert result.failures == []
    assert result.telemetry["state"]["topology"]["links_up"]["r1:eth0<->r2:eth0"] is True
    assert result.telemetry["state"]["bgp_peers"]["r1<->r2"] is True
    assert result.telemetry["state"]["last_recovered_link"] == {"a": "r1:eth0", "b": "r2:eth0"}
    assert result.telemetry["state"]["bgp_peer_recovered"] == {"node": "r1", "peer": "r2"}


def test_runner_rejects_recover_link_for_unknown_topology_link() -> None:
    runner = ScenarioRunner(capability_matrix=_matrix())
    scenario = Scenario(
        name="unknown-recover-link",
        lab_id="lab16",
        topology=TopologySpec(nodes=("r1", "r2"), links=(("r1:eth0", "r2:eth0"),)),
        actions=[ScenarioAction(at_ms=100, action="recover_link", params={"a": "r1:eth9", "b": "r2:eth9"})],
        expectations=[],
    )

    with pytest.raises(ValueError, match="unknown endpoint"):
        runner.run(scenario)


def test_runner_rejects_recover_bgp_peer_for_unknown_node() -> None:
    runner = ScenarioRunner(capability_matrix=_matrix())
    scenario = Scenario(
        name="unknown-recover-bgp-peer",
        lab_id="lab16",
        topology=TopologySpec(nodes=("r1", "r2"), links=(("r1:eth0", "r2:eth0"),)),
        actions=[ScenarioAction(at_ms=100, action="recover_bgp_peer", params={"node": "r1", "peer": "r9"})],
        expectations=[],
    )

    with pytest.raises(ValueError, match="unknown node"):
        runner.run(scenario)
