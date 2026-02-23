"""Scenario file loading and report rendering helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pycie.scenario.dsl import Expectation, Scenario, ScenarioAction, TopologySpec
from pycie.scenario.runner import ScenarioResult


def load_scenario(path: str | Path) -> Scenario:
    """Load one scenario JSON file into typed dataclasses."""
    scenario_path = Path(path)
    raw = json.loads(scenario_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("scenario file must decode to an object")

    name = _expect_str(raw, "name")
    lab_id = _expect_str(raw, "lab_id")

    topology_raw = _expect_dict(raw, "topology")
    nodes = _expect_str_list(topology_raw, "nodes")
    links_raw = topology_raw.get("links")
    if not isinstance(links_raw, list):
        raise ValueError("topology.links must be a list")
    links: list[tuple[str, str]] = []
    for item in links_raw:
        if not isinstance(item, list) or len(item) != 2:
            raise ValueError("each topology.links entry must be [left, right]")
        left, right = item
        if not isinstance(left, str) or not isinstance(right, str):
            raise ValueError("topology link endpoints must be strings")
        links.append((left, right))

    actions_raw = raw.get("actions", [])
    if not isinstance(actions_raw, list):
        raise ValueError("actions must be a list")
    actions: list[ScenarioAction] = []
    for action_raw in actions_raw:
        if not isinstance(action_raw, dict):
            raise ValueError("each action must be an object")
        at_ms = int(action_raw.get("at_ms", 0))
        action = _expect_str(action_raw, "action")
        params_raw = action_raw.get("params", {})
        if not isinstance(params_raw, dict):
            raise ValueError("action params must be an object")
        actions.append(ScenarioAction(at_ms=at_ms, action=action, params=params_raw))

    expectations_raw = raw.get("expectations", [])
    if not isinstance(expectations_raw, list):
        raise ValueError("expectations must be a list")
    expectations: list[Expectation] = []
    for expectation_raw in expectations_raw:
        if not isinstance(expectation_raw, dict):
            raise ValueError("each expectation must be an object")
        kind = _expect_str(expectation_raw, "kind")
        selector = _expect_str(expectation_raw, "selector")
        expectations.append(
            Expectation(
                kind=kind,
                selector=selector,
                expected=expectation_raw.get("expected"),
            )
        )

    metadata_raw = raw.get("metadata", {})
    if metadata_raw is None:
        metadata: dict[str, Any] = {}
    elif isinstance(metadata_raw, dict):
        metadata = metadata_raw
    else:
        raise ValueError("metadata must be an object when provided")

    return Scenario(
        name=name,
        lab_id=lab_id,
        topology=TopologySpec(nodes=tuple(nodes), links=tuple(links)),
        actions=actions,
        expectations=expectations,
        metadata=metadata,
    )


def render_scenario_report(
    scenario: Scenario,
    result: ScenarioResult,
    *,
    report_format: str,
) -> str:
    """Render scenario result report as json or markdown."""
    fmt = report_format.strip().lower()
    if fmt == "json":
        payload = {
            "name": scenario.name,
            "lab_id": scenario.lab_id,
            "passed": result.passed,
            "actions": len(scenario.actions),
            "expectations": len(scenario.expectations),
            "failures": list(result.failures),
            "telemetry": result.telemetry,
        }
        return json.dumps(payload, indent=2, sort_keys=True) + "\n"

    if fmt == "md":
        status = "PASS" if result.passed else "FAIL"
        lines = [
            f"# Scenario Report: {scenario.name}",
            "",
            f"- Lab: `{scenario.lab_id}`",
            f"- Status: `{status}`",
            f"- Actions: `{len(scenario.actions)}`",
            f"- Expectations: `{len(scenario.expectations)}`",
        ]
        if result.failures:
            lines.extend(
                [
                    "",
                    "## Failures",
                    "",
                ]
            )
            for failure in result.failures:
                lines.append(f"- {failure}")
        lines.append("")
        return "\n".join(lines)

    raise ValueError("report format must be one of: json, md")


def _expect_dict(container: dict[str, Any], key: str) -> dict[str, Any]:
    value = container.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    return value


def _expect_str(container: dict[str, Any], key: str) -> str:
    value = container.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _expect_str_list(container: dict[str, Any], key: str) -> list[str]:
    value = container.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item:
            raise ValueError(f"{key} entries must be non-empty strings")
        items.append(item)
    return items
