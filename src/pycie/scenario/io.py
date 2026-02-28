"""Scenario file loading and report rendering helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pycie.scenario.dsl import (
    Expectation,
    ExpectationKind,
    Scenario,
    ScenarioAction,
    ScenarioActionType,
    TopologySpec,
)
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
    for idx, action_raw in enumerate(actions_raw):
        if not isinstance(action_raw, dict):
            raise ValueError(f"actions[{idx}] must be an object")
        at_ms_raw = action_raw.get("at_ms", 0)
        if not isinstance(at_ms_raw, int) or isinstance(at_ms_raw, bool):
            raise ValueError(f"actions[{idx}].at_ms must be an integer")
        if at_ms_raw < 0:
            raise ValueError(f"actions[{idx}].at_ms must be >= 0")
        action = _expect_str(action_raw, "action")
        try:
            action_enum = ScenarioActionType(action)
        except ValueError as exc:
            supported = ", ".join(sorted(item.value for item in ScenarioActionType))
            raise ValueError(
                f"actions[{idx}].action {action!r} is unsupported; supported actions: {supported}"
            ) from exc
        params_raw = action_raw.get("params", {})
        if not isinstance(params_raw, dict):
            raise ValueError(f"actions[{idx}].params must be an object")
        _validate_action_params(idx, action_enum, params_raw)
        actions.append(ScenarioAction(at_ms=at_ms_raw, action=action_enum.value, params=params_raw))

    expectations_raw = raw.get("expectations", [])
    if not isinstance(expectations_raw, list):
        raise ValueError("expectations must be a list")
    expectations: list[Expectation] = []
    for idx, expectation_raw in enumerate(expectations_raw):
        if not isinstance(expectation_raw, dict):
            raise ValueError(f"expectations[{idx}] must be an object")
        kind = _expect_str(expectation_raw, "kind")
        try:
            kind_enum = ExpectationKind(kind)
        except ValueError as exc:
            supported = ", ".join(sorted(item.value for item in ExpectationKind))
            raise ValueError(
                f"expectations[{idx}].kind {kind!r} is unsupported; supported kinds: {supported}"
            ) from exc
        selector = _expect_str(expectation_raw, "selector")
        if "expected" not in expectation_raw:
            raise ValueError(f"expectations[{idx}].expected is required")
        expected = expectation_raw["expected"]
        _validate_expectation_expected(idx, kind_enum, expected)
        expectations.append(
            Expectation(
                kind=kind_enum.value,
                selector=selector,
                expected=expected,
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
            "action_timeline": _timeline_payload(result),
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
        lines.extend(_render_action_timeline(result))
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


def _render_action_timeline(result: ScenarioResult) -> list[str]:
    rows = _timeline_rows(result)
    lines = [
        "",
        "## Action Timeline",
        "",
        "| timestamp_ms | action | key_state_change |",
        "| ---: | --- | --- |",
    ]
    if not rows:
        lines.append("| n/a | n/a | no events recorded |")
        return lines

    for at_ms, action, state_change in rows:
        lines.append(
            "| "
            f"{_md_cell(at_ms)} | "
            f"`{_md_cell(action)}` | "
            f"{_md_cell(state_change)} |"
        )
    return lines


def _timeline_payload(result: ScenarioResult) -> list[dict[str, str]]:
    rows = _timeline_rows(result)
    payload: list[dict[str, str]] = []
    for at_ms, action, state_change in rows:
        payload.append(
            {
                "timestamp_ms": at_ms,
                "action": action,
                "key_state_change": state_change,
            }
        )
    return payload


def _timeline_rows(result: ScenarioResult) -> list[tuple[str, str, str]]:
    telemetry = result.telemetry if isinstance(result.telemetry, dict) else {}
    events = telemetry.get("events", [])
    if not isinstance(events, list):
        return []
    rows: list[tuple[str, str, str]] = []
    for event in events:
        if not isinstance(event, dict):
            continue
        action_raw = event.get("action", "")
        action = action_raw if isinstance(action_raw, str) else str(action_raw)
        params_raw = event.get("params", {})
        params = params_raw if isinstance(params_raw, dict) else {}
        at_ms_value = params.get("_at_ms")
        at_ms = (
            str(at_ms_value)
            if isinstance(at_ms_value, int) and not isinstance(at_ms_value, bool)
            else "n/a"
        )
        rows.append((at_ms, action, _summarize_action_state_change(action, params)))
    return rows


def _summarize_action_state_change(action: str, params: dict[str, Any]) -> str:
    if action in {ScenarioActionType.FAIL_LINK.value, ScenarioActionType.RECOVER_LINK.value}:
        left = _string_param(params, "a")
        right = _string_param(params, "b")
        state = "down" if action == ScenarioActionType.FAIL_LINK.value else "up"
        if left and right:
            return f"link `{left}<->{right}` -> `{state}`"
        return f"link state -> `{state}`"

    if action in {ScenarioActionType.FAIL_BGP_PEER.value, ScenarioActionType.RECOVER_BGP_PEER.value}:
        node = _string_param(params, "node")
        peer = _string_param(params, "peer")
        state = "down" if action == ScenarioActionType.FAIL_BGP_PEER.value else "up"
        if node and peer:
            return f"BGP peer `{node}<->{peer}` -> `{state}`"
        return f"BGP peer state -> `{state}`"

    if action in {ScenarioActionType.ROUTE_SET_PRESENT.value, ScenarioActionType.ROUTE_SET_ABSENT.value}:
        selector = _string_param(params, "selector")
        state = "present" if action == ScenarioActionType.ROUTE_SET_PRESENT.value else "absent"
        if selector:
            return f"route `{selector}` -> `{state}`"
        return f"route state -> `{state}`"

    if action == ScenarioActionType.MARK_CONVERGED.value:
        return "convergence marked complete"

    param_items = [
        f"{key}={value!r}"
        for key, value in sorted(params.items())
        if key != "_at_ms"
    ]
    if param_items:
        return ", ".join(param_items)
    return "state updated"


def _string_param(params: dict[str, Any], key: str) -> str | None:
    value = params.get(key)
    if isinstance(value, str) and value:
        return value
    return None


def _md_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _validate_action_params(idx: int, action: ScenarioActionType, params: dict[str, Any]) -> None:
    required_by_action: dict[ScenarioActionType, tuple[str, ...]] = {
        ScenarioActionType.FAIL_LINK: ("a", "b"),
        ScenarioActionType.RECOVER_LINK: ("a", "b"),
        ScenarioActionType.FAIL_BGP_PEER: ("node", "peer"),
        ScenarioActionType.RECOVER_BGP_PEER: ("node", "peer"),
        ScenarioActionType.ROUTE_SET_PRESENT: ("selector",),
        ScenarioActionType.ROUTE_SET_ABSENT: ("selector",),
        ScenarioActionType.MARK_CONVERGED: (),
    }

    required = required_by_action[action]
    allowed = set(required)
    for key in required:
        value = params.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(
                f"actions[{idx}].params.{key} must be a non-empty string for action {action.value!r}"
            )
    for key in sorted(params):
        if key not in allowed:
            raise ValueError(f"actions[{idx}].params.{key} is not supported for action {action.value!r}")


def _validate_expectation_expected(idx: int, kind: ExpectationKind, expected: Any) -> None:
    if kind in {ExpectationKind.EVENT_SEEN, ExpectationKind.ROUTE_PRESENT}:
        if not isinstance(expected, bool):
            raise ValueError(f"expectations[{idx}].expected must be a boolean for kind {kind.value!r}")
        return

    if kind == ExpectationKind.CONVERGENCE_MS_LTE:
        if not isinstance(expected, int) or isinstance(expected, bool):
            raise ValueError(f"expectations[{idx}].expected must be an integer for kind {kind.value!r}")
        if expected < 0:
            raise ValueError(f"expectations[{idx}].expected must be >= 0 for kind {kind.value!r}")
        return


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
