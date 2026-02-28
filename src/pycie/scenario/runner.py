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
        self._known_nodes = set(scenario.topology.nodes)
        self._known_links = {
            self._normalized_link(left, right)
            for left, right in scenario.topology.links
        }
        self._events: list[dict[str, Any]] = []
        self._state: dict[str, Any] = {
            "routes": self._initial_routes(scenario.metadata),
            "topology": {
                "nodes": sorted(self._known_nodes),
                "links_up": {
                    self._link_key(link): True
                    for link in sorted(self._known_links)
                },
            },
            "bgp_peers": {},
            "convergence": {
                "failure_start_ms": None,
                "converged_at_ms": None,
                "last_action_ms": None,
            },
        }

        for action in sorted(scenario.actions, key=lambda a: a.at_ms):
            params = dict(action.params)
            params["_at_ms"] = action.at_ms
            self.apply_action(action.action, params)

        convergence_ms = self._convergence_ms()
        self._state["convergence"]["elapsed_ms"] = convergence_ms

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
        event = {"action": str(action_enum), "params": dict(params)}
        self._events.append(event)
        at_ms = int(params.get("_at_ms", 0))
        convergence = self._state["convergence"]
        convergence["last_action_ms"] = at_ms

        if action_enum == ScenarioActionType.FAIL_LINK:
            left = self._expect_endpoint(params, "a")
            right = self._expect_endpoint(params, "b")
            link = self._normalized_link(left, right)
            if link not in self._known_links:
                raise ValueError(f"fail_link references unknown link {left!r} <-> {right!r}")
            if convergence["failure_start_ms"] is None:
                convergence["failure_start_ms"] = at_ms
            self._state["topology"]["links_up"][self._link_key(link)] = False
            self._state["last_failed_link"] = {"a": left, "b": right}
            return

        if action_enum == ScenarioActionType.RECOVER_LINK:
            left = self._expect_endpoint(params, "a")
            right = self._expect_endpoint(params, "b")
            link = self._normalized_link(left, right)
            if link not in self._known_links:
                raise ValueError(f"recover_link references unknown link {left!r} <-> {right!r}")
            self._state["topology"]["links_up"][self._link_key(link)] = True
            self._state["last_recovered_link"] = {"a": left, "b": right}
            return

        if action_enum == ScenarioActionType.FAIL_BGP_PEER:
            node = self._expect_node(params, "node")
            peer = self._expect_node(params, "peer")
            peer_pair = self._normalized_link(node, peer)
            if convergence["failure_start_ms"] is None:
                convergence["failure_start_ms"] = at_ms
            self._state["bgp_peers"][self._link_key(peer_pair)] = False
            self._state["bgp_peer_failed"] = {
                "node": node,
                "peer": peer,
            }
            return

        if action_enum == ScenarioActionType.RECOVER_BGP_PEER:
            node = self._expect_node(params, "node")
            peer = self._expect_node(params, "peer")
            peer_pair = self._normalized_link(node, peer)
            self._state["bgp_peers"][self._link_key(peer_pair)] = True
            self._state["bgp_peer_recovered"] = {
                "node": node,
                "peer": peer,
            }
            return

        if action_enum == ScenarioActionType.ROUTE_SET_PRESENT:
            selector = self._expect_route_selector(params)
            self._state["routes"][selector] = True
            return

        if action_enum == ScenarioActionType.ROUTE_SET_ABSENT:
            selector = self._expect_route_selector(params)
            self._state["routes"][selector] = False
            return

        if action_enum == ScenarioActionType.MARK_CONVERGED:
            convergence["converged_at_ms"] = at_ms
            return

    def evaluate_expectation(
        self,
        kind: "ExpectationKind | str",
        selector: str,
        expected: Any,
    ) -> tuple[bool, str | None]:
        """Return (ok, failure_message) for one expectation."""
        expectation_kind = ExpectationKind(kind)

        if expectation_kind == ExpectationKind.EVENT_SEEN:
            seen = any(str(event.get("action")) == selector for event in self._events)
            ok = seen == bool(expected)
            if ok:
                return True, None
            return (
                False,
                "expectation failed: kind=event_seen "
                f"selector={selector!r} expected={expected} actual={seen}",
            )

        if expectation_kind == ExpectationKind.CONVERGENCE_MS_LTE:
            convergence_ms = self._convergence_ms()
            if convergence_ms is None:
                return (
                    False,
                    "expectation failed: kind=convergence_ms_lte "
                    f"selector={selector!r} expected_lte={expected} actual=unconverged",
                )
            ok = convergence_ms <= int(expected)
            if ok:
                return True, None
            return (
                False,
                "expectation failed: kind=convergence_ms_lte "
                f"selector={selector!r} expected_lte={expected} actual={convergence_ms}",
            )

        if expectation_kind == ExpectationKind.ROUTE_PRESENT:
            present = bool(self._state["routes"].get(selector, False))
            ok = present == bool(expected)
            if ok:
                return True, None
            return (
                False,
                "expectation failed: kind=route_present "
                f"selector={selector!r} expected={expected} actual={present}",
            )

        return False, f"unsupported expectation kind {expectation_kind!r} selector={selector!r}"

    def _convergence_ms(self) -> int | None:
        """Compute convergence elapsed time from first disruption to convergence mark."""
        convergence = self._state["convergence"]
        start = convergence.get("failure_start_ms")
        converged_at = convergence.get("converged_at_ms")
        if start is None:
            return 0
        if converged_at is None:
            return None
        return max(0, int(converged_at) - int(start))

    @staticmethod
    def _expect_route_selector(params: dict[str, Any]) -> str:
        selector = params.get("selector")
        if not isinstance(selector, str) or not selector:
            raise ValueError("route_set_present/route_set_absent requires params.selector")
        return selector

    def _expect_endpoint(self, params: dict[str, Any], key: str) -> str:
        endpoint = params.get(key)
        if not isinstance(endpoint, str) or not endpoint:
            raise ValueError(f"{key} must be a non-empty endpoint string")
        if endpoint not in {value for link in self._known_links for value in link}:
            raise ValueError(f"unknown endpoint {endpoint!r}")
        return endpoint

    def _expect_node(self, params: dict[str, Any], key: str) -> str:
        node = params.get(key)
        if not isinstance(node, str) or not node:
            raise ValueError(f"{key} must be a non-empty node id")
        if node not in self._known_nodes:
            raise ValueError(f"unknown node {node!r}")
        return node

    @staticmethod
    def _normalized_link(left: str, right: str) -> tuple[str, str]:
        return (left, right) if left <= right else (right, left)

    @staticmethod
    def _link_key(link: tuple[str, str]) -> str:
        return f"{link[0]}<->{link[1]}"

    @staticmethod
    def _initial_routes(metadata: dict[str, Any]) -> dict[str, bool]:
        routes_raw = metadata.get("initial_routes", {})
        if routes_raw is None:
            return {}
        if not isinstance(routes_raw, dict):
            raise ValueError("metadata.initial_routes must be an object")
        routes: dict[str, bool] = {}
        for selector, present in routes_raw.items():
            if not isinstance(selector, str) or not selector:
                raise ValueError("metadata.initial_routes keys must be non-empty strings")
            routes[selector] = bool(present)
        return routes
