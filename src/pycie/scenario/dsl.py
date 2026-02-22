"""Declarative scenario objects for convergence/failure exercises."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TopologySpec:
    nodes: tuple[str, ...]
    links: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class ScenarioAction:
    at_ms: int
    action: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Expectation:
    kind: str
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
