"""Lab 01: learning switch protocol scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field

from pycie.sim.network import Frame

from .base import ProtocolBase


@dataclass(frozen=True)
class MacEntry:
    mac: str
    interface: str
    learned_at_ms: float


@dataclass
class LearningSwitch(ProtocolBase):
    """Simplified L2 learning switch behavior.

    Reading:
    - IEEE 802.1D bridge behavior
    - RFC 1812 section on forwarding principles (for mindset)
    """

    name: str = "switching"
    mac_aging_ms: float = 300_000.0
    mac_table: dict[str, MacEntry] = field(default_factory=dict)

    def on_frame(self, ingress_if: str, frame: Frame) -> None:
        """Learn source MAC and forward/flood based on destination lookup."""
        self.age_mac_table()
        self.learn_source_mac(ingress_if, frame.src_mac)
        egress_interfaces = self.lookup_egress_interfaces(ingress_if, frame.dst_mac)
        for egress_if in egress_interfaces:
            self.device.send_frame(egress_if, frame)

    def learn_source_mac(self, ingress_if: str, src_mac: str) -> None:
        """Install or refresh a source-MAC entry in the local table."""
        self.mac_table[src_mac] = MacEntry(
            mac=src_mac,
            interface=ingress_if,
            learned_at_ms=self.now_ms,
        )

    def lookup_egress_interfaces(self, ingress_if: str, dst_mac: str) -> list[str]:
        """Return output interfaces for destination MAC (unicast or flood set)."""
        if self.should_flood(dst_mac):
            return sorted(if_name for if_name in self.device.interfaces if if_name != ingress_if)

        entry = self.mac_table.get(dst_mac)
        if entry is None:
            return sorted(if_name for if_name in self.device.interfaces if if_name != ingress_if)
        if entry.interface == ingress_if:
            return []
        return [entry.interface]

    def age_mac_table(self) -> None:
        """Expire stale MAC entries based on current simulation time."""
        expired = [
            mac
            for mac, entry in self.mac_table.items()
            if self.now_ms - entry.learned_at_ms >= self.mac_aging_ms
        ]
        for mac in expired:
            del self.mac_table[mac]

    def should_flood(self, dst_mac: str) -> bool:
        """Return True for unknown unicast and broadcast destinations."""
        if dst_mac.lower() == "ff:ff:ff:ff:ff:ff":
            return True
        return dst_mac not in self.mac_table
