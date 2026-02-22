"""Scenario runner scaffold binding DSL to simulation objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pycie.model.capabilities import CapabilityMatrix
from pycie.scenario.dsl import ExpectationKind, Scenario, ScenarioActionType


@dataclass
class ScenarioResult:
    passed: bool
    failures: list[str] = field(default_factory=list)
    telemetry: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScenarioRunner:
    """Execute scenario actions and evaluate expectations."""

    capability_matrix: CapabilityMatrix

    def run(self, scenario: Scenario) -> ScenarioResult:
        """Run a full scenario and evaluate all expectations."""
        self.capability_matrix.for_lab(scenario.lab_id)
        self._events: list[dict[str, Any]] = []
        self._state: dict[str, Any] = {}

        for action in sorted(scenario.actions, key=lambda a: a.at_ms):
            params = dict(action.params)
            params["_at_ms"] = action.at_ms
            self.apply_action(action.action, params)

        failures: list[str] = []
        for expectation in scenario.expectations:
            ok, failure = self.evaluate_expectation(
                expectation.kind,
                expectation.selector,
                expectation.expected,
            )
            if not ok and failure is not None:
                failures.append(failure)

        return ScenarioResult(
            passed=not failures,
            failures=failures,
            telemetry={"events": list(self._events), "state": dict(self._state)},
        )

    def apply_action(self, action: "ScenarioActionType | str", params: dict[str, Any]) -> None:
        """Apply a single scenario action to sim/topology/protocol state."""
        action_enum = ScenarioActionType(action)
        event = {"action": action_enum, "params": dict(params)}
        self._events.append(event)

        if action_enum == ScenarioActionType.FAIL_LINK:
            self._state["last_failed_link"] = (params.get("a"), params.get("b"))
        if action_enum == ScenarioActionType.FAIL_BGP_PEER:
            self._state["bgp_peer_failed"] = (params.get("node"), params.get("peer"))

    def evaluate_expectation(
        self,
        kind: "ExpectationKind | str",
        selector: str,
        expected: Any,
    ) -> tuple[bool, str | None]:
        """Return (ok, failure_message) for one expectation."""
        expectation_kind = ExpectationKind(kind)

        if expectation_kind == ExpectationKind.EVENT_SEEN:
            seen = any(event.get("action") == selector for event in self._events)
            ok = seen == bool(expected)
            if ok:
                return True, None
            return False, f"expected event_seen={expected} for {selector!r}, got {seen}"

        if expectation_kind == ExpectationKind.CONVERGENCE_MS_LTE:
            # Baseline convergence model assumes immediate logical convergence.
            convergence_ms = 0
            ok = convergence_ms <= int(expected)
            if ok:
                return True, None
            return False, f"convergence {convergence_ms}ms exceeds {expected}ms"

        if expectation_kind == ExpectationKind.ROUTE_PRESENT:
            # Placeholder route check hook for future simulator integration.
            present = True
            ok = present == bool(expected)
            if ok:
                return True, None
            return False, f"route presence for {selector!r} expected {expected}, got {present}"

        return False, f"unsupported expectation kind {expectation_kind!r}"
