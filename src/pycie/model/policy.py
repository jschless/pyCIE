"""Route policy data structures for BGP/VRF labs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MatchConditions:
    """Match criteria for a route policy rule."""

    prefix: str | None = None
    community: str | None = None
    neighbor: str | None = None
    min_as_path_len: int | None = None
    max_as_path_len: int | None = None


@dataclass(frozen=True)
class PolicyAction:
    """Mutations or permit/deny outcome for a matched rule."""

    permit: bool = True
    set_local_pref: int | None = None
    set_med: int | None = None
    prepend_asn: int | None = None
    prepend_count: int = 0
    add_community: str | None = None


@dataclass(frozen=True)
class RoutePolicyRule:
    sequence: int
    matches: MatchConditions
    action: PolicyAction


@dataclass
class RoutePolicy:
    """Ordered route policy evaluation pipeline."""

    name: str
    rules: list[RoutePolicyRule] = field(default_factory=list)

    def evaluate(self, route: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        """Return (permitted, possibly-mutated route attributes)."""
        current = dict(route)
        if "as_path" in current:
            current["as_path"] = list(current["as_path"])

        for rule in sorted(self.rules, key=lambda item: item.sequence):
            if not self.matches(current, rule.matches):
                continue
            mutated = self.apply_action(current, rule.action)
            return rule.action.permit, mutated

        return False, current

    def matches(self, route: dict[str, Any], cond: MatchConditions) -> bool:
        """Return whether route attributes satisfy given match conditions."""
        if cond.prefix is not None and route.get("prefix") != cond.prefix:
            return False
        if cond.community is not None and route.get("community") != cond.community:
            return False
        if cond.neighbor is not None and route.get("neighbor") != cond.neighbor:
            return False

        as_path = route.get("as_path", [])
        if cond.min_as_path_len is not None and len(as_path) < cond.min_as_path_len:
            return False
        if cond.max_as_path_len is not None and len(as_path) > cond.max_as_path_len:
            return False
        return True

    def apply_action(self, route: dict[str, Any], action: PolicyAction) -> dict[str, Any]:
        """Return route copy with action mutations applied."""
        out = dict(route)
        if "as_path" in out:
            out["as_path"] = list(out["as_path"])

        if action.set_local_pref is not None:
            out["local_pref"] = action.set_local_pref
        if action.set_med is not None:
            out["med"] = action.set_med
        if action.prepend_asn is not None and action.prepend_count > 0:
            as_path = list(out.get("as_path", []))
            as_path = [action.prepend_asn] * action.prepend_count + as_path
            out["as_path"] = as_path
        if action.add_community is not None:
            current = out.get("community")
            if not current:
                out["community"] = action.add_community
            elif isinstance(current, str):
                out["community"] = f"{current},{action.add_community}"
        return out
