"""Lab 13: route-policy engine scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pycie.model.policy import RoutePolicy

from .base import ProtocolBase


@dataclass
class PolicyProcess(ProtocolBase):
    """Policy application for import/export route pipelines."""

    name: str = "policy"
    import_policies: dict[str, list[RoutePolicy]] = field(default_factory=dict)
    export_policies: dict[str, list[RoutePolicy]] = field(default_factory=dict)

    def apply_import(self, neighbor: str, route: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        """Run import policy chain for neighbor and return permit/route."""
        current = dict(route)
        if "as_path" in current:
            current["as_path"] = list(current["as_path"])

        for policy in self.import_policies.get(neighbor, []):
            permitted, current = policy.evaluate(current)
            if not permitted:
                return False, current
        return True, current

    def apply_export(self, neighbor: str, route: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        """Run export policy chain for neighbor and return permit/route."""
        current = dict(route)
        if "as_path" in current:
            current["as_path"] = list(current["as_path"])

        for policy in self.export_policies.get(neighbor, []):
            permitted, current = policy.evaluate(current)
            if not permitted:
                return False, current
        return True, current
