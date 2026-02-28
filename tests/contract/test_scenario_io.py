"""Contract tests for scenario schema validation and report rendering."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from pycie.scenario import load_scenario, render_scenario_report
from pycie.scenario.dsl import Scenario, TopologySpec
from pycie.scenario.runner import ScenarioResult


def _write_scenario(tmp_path: Path, payload: dict[str, Any]) -> Path:
    path = tmp_path / "scenario.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _base_payload() -> dict[str, Any]:
    return {
        "name": "schema-check",
        "lab_id": "lab16",
        "topology": {
            "nodes": ["r1", "r2"],
            "links": [["r1:eth0", "r2:eth0"]],
        },
        "actions": [],
        "expectations": [
            {
                "kind": "event_seen",
                "selector": "fail_link",
                "expected": False,
            }
        ],
    }


def test_load_scenario_rejects_unsupported_action(tmp_path: Path) -> None:
    payload = _base_payload()
    payload["actions"] = [{"at_ms": 100, "action": "break_world", "params": {}}]

    with pytest.raises(ValueError, match="unsupported"):
        load_scenario(_write_scenario(tmp_path, payload))


def test_load_scenario_rejects_missing_action_param(tmp_path: Path) -> None:
    payload = _base_payload()
    payload["actions"] = [
        {"at_ms": 100, "action": "fail_link", "params": {"a": "r1:eth0"}},
    ]

    with pytest.raises(ValueError, match=r"actions\[0\]\.params\.b must be a non-empty string"):
        load_scenario(_write_scenario(tmp_path, payload))


def test_load_scenario_rejects_invalid_expected_type_for_convergence(tmp_path: Path) -> None:
    payload = _base_payload()
    payload["expectations"] = [
        {
            "kind": "convergence_ms_lte",
            "selector": "fabric",
            "expected": True,
        }
    ]

    with pytest.raises(ValueError, match="must be an integer"):
        load_scenario(_write_scenario(tmp_path, payload))


def test_render_markdown_report_includes_action_timeline_table() -> None:
    scenario = Scenario(
        name="timeline",
        lab_id="lab16",
        topology=TopologySpec(nodes=("r1", "r2"), links=(("r1:eth0", "r2:eth0"),)),
    )
    result = ScenarioResult(
        passed=True,
        failures=[],
        telemetry={
            "events": [
                {
                    "action": "fail_link",
                    "params": {"_at_ms": 10, "a": "r1:eth0", "b": "r2:eth0"},
                },
                {
                    "action": "mark_converged",
                    "params": {"_at_ms": 40},
                },
            ],
            "state": {},
        },
    )

    report = render_scenario_report(scenario, result, report_format="md")
    assert "## Action Timeline" in report
    assert "| timestamp_ms | action | key_state_change |" in report
    assert "`fail_link`" in report
    assert "link `r1:eth0<->r2:eth0` -> `down`" in report
    assert "`mark_converged`" in report


def test_render_json_report_includes_action_timeline_payload() -> None:
    scenario = Scenario(
        name="timeline-json",
        lab_id="lab16",
        topology=TopologySpec(nodes=("r1", "r2"), links=(("r1:eth0", "r2:eth0"),)),
    )
    result = ScenarioResult(
        passed=True,
        failures=[],
        telemetry={
            "events": [
                {
                    "action": "recover_bgp_peer",
                    "params": {"_at_ms": 120, "node": "r1", "peer": "r2"},
                }
            ],
            "state": {},
        },
    )

    report = render_scenario_report(scenario, result, report_format="json")
    payload = json.loads(report)
    assert payload["action_timeline"] == [
        {
            "timestamp_ms": "120",
            "action": "recover_bgp_peer",
            "key_state_change": "BGP peer `r1<->r2` -> `up`",
        }
    ]
