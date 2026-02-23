"""Capability matrix for gating lab behavior and tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass(frozen=True)
class CapabilitySet:
    """Feature flags enabled for a given lab or scenario."""

    switching: bool = False
    stp: bool = False
    ospf: bool = False
    bgp: bool = False
    ldp: bool = False
    bfd: bool = False
    ipv4_forwarding: bool = False
    arp: bool = False
    vlan: bool = False
    rstp: bool = False
    gre: bool = False
    ipsec: bool = False
    vrf: bool = False
    mpls_forwarding: bool = False
    policy: bool = False
    telemetry: bool = False
    isis: bool = False
    route_selection: bool = False
    redistribution: bool = False
    acl: bool = False
    aaa: bool = False
    dhcp: bool = False
    multicast: bool = False
    vxlan: bool = False
    evpn: bool = False
    macsec: bool = False
    control_plane_db: bool = False
    rib_fib_pipeline: bool = False
    bgp_fsm_transport: bool = False
    ospf_multi_area: bool = False
    ikev2: bool = False
    ipv6_nd: bool = False
    nat44: bool = False

    def require(self, feature: str) -> None:
        """Raise if a feature is unavailable in this capability set."""
        enabled = getattr(self, feature, None)
        if enabled is None:
            raise KeyError(f"unknown capability {feature!r}")
        if not enabled:
            raise RuntimeError(f"capability {feature!r} is disabled in this lab")


@dataclass
class CapabilityMatrix:
    """Lab -> capability mapping used by tests and scenario runner."""

    per_lab: dict[str, CapabilitySet] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: dict[str, dict[str, bool]]) -> "CapabilityMatrix":
        matrix = cls()
        for lab_id, values in raw.items():
            matrix.per_lab[lab_id] = CapabilitySet(**values)
        return matrix

    @classmethod
    def from_json(cls, path: str | Path) -> "CapabilityMatrix":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(data)

    def for_lab(self, lab_id: str) -> CapabilitySet:
        if lab_id not in self.per_lab:
            raise KeyError(f"unknown lab {lab_id!r}")
        return self.per_lab[lab_id]
