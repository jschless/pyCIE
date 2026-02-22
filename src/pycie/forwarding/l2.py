"""VLAN-aware Layer-2 forwarding scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from pycie.model.headers import Dot1QHeader
from pycie.model.packet import PacketStack


class BridgePortMode(StrEnum):
    ACCESS = "access"
    TRUNK = "trunk"


@dataclass(frozen=True)
class BridgePort:
    """Bridge port access/trunk configuration."""

    if_name: str
    mode: "BridgePortMode | str" = BridgePortMode.ACCESS
    access_vlan: int = 1
    allowed_vlans: frozenset[int] = frozenset({1})
    native_vlan: int | None = 1


@dataclass
class BridgeDomain:
    """L2 bridge domain with VLAN filtering and FDB learning."""

    ports: dict[str, BridgePort] = field(default_factory=dict)
    fdb: dict[tuple[int, str], str] = field(default_factory=dict)
    mac_aging_ms: int = 300_000
    learned_at_ms: dict[tuple[int, str], float] = field(default_factory=dict)

    def register_port(self, port: BridgePort) -> None:
        self.ports[port.if_name] = port

    def ingress_vlan(self, ingress_if: str, packet: PacketStack) -> int | None:
        """Return ingress VLAN ID for packet on given port, or None if drop."""
        port = self.ports.get(ingress_if)
        if port is None:
            return None

        tag = next((h for h in packet.headers if isinstance(h, Dot1QHeader)), None)

        mode = BridgePortMode(port.mode)

        if mode == BridgePortMode.ACCESS:
            if tag is not None:
                return None
            return port.access_vlan

        if mode != BridgePortMode.TRUNK:
            return None

        if tag is not None:
            vlan = tag.vlan_id
        else:
            if port.native_vlan is None:
                return None
            vlan = port.native_vlan

        if vlan not in port.allowed_vlans:
            return None
        return vlan

    def learn(self, vlan: int, src_mac: str, ingress_if: str, now_ms: float) -> None:
        """Learn or refresh source MAC for VLAN in FDB."""
        key = (vlan, src_mac)
        self.fdb[key] = ingress_if
        self.learned_at_ms[key] = now_ms

    def lookup_egress(self, vlan: int, dst_mac: str, ingress_if: str) -> list[str]:
        """Return egress ports for destination in VLAN context."""
        key = (vlan, dst_mac)
        learned_if = self.fdb.get(key)
        if learned_if is not None and learned_if != ingress_if:
            return [learned_if]

        flood_set: list[str] = []
        for if_name, port in sorted(self.ports.items()):
            if if_name == ingress_if:
                continue
            mode = BridgePortMode(port.mode)
            if mode == BridgePortMode.ACCESS and port.access_vlan == vlan:
                flood_set.append(if_name)
            if mode == BridgePortMode.TRUNK and vlan in port.allowed_vlans:
                flood_set.append(if_name)
        return flood_set

    def egress_should_tag(self, egress_if: str, vlan: int) -> bool:
        """Return True when VLAN should be tagged on egress trunk."""
        port = self.ports[egress_if]
        if BridgePortMode(port.mode) == BridgePortMode.ACCESS:
            return False
        return port.native_vlan != vlan

    def age_fdb(self, now_ms: float) -> None:
        """Expire stale FDB entries using configured aging interval."""
        expired = [
            key
            for key, learned_at in self.learned_at_ms.items()
            if now_ms - learned_at >= self.mac_aging_ms
        ]
        for key in expired:
            self.learned_at_ms.pop(key, None)
            self.fdb.pop(key, None)
