"""Declarative scenario objects for convergence/failure exercises."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ScenarioActionType(StrEnum):
    FAIL_LINK = "fail_link"
    FAIL_BGP_PEER = "fail_bgp_peer"


class ExpectationKind(StrEnum):
    EVENT_SEEN = "event_seen"
    CONVERGENCE_MS_LTE = "convergence_ms_lte"
    ROUTE_PRESENT = "route_present"


@dataclass(frozen=True)
class TopologySpec:
    nodes: tuple[str, ...]
    links: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class ScenarioAction:
    at_ms: int
    action: "ScenarioActionType | str"
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Expectation:
    kind: "ExpectationKind | str"
    selector: str
    expected: Any


@dataclass
class Scenario:
    """A runnable scenario with actions and postconditions."""

    name: str
    lab_id: str
    topology: TopologySpec
    actions: list[ScenarioAction] = field(default_factory=list)
    expectations: list[Expectation] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
