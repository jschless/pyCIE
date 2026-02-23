"""Lab 01: learning switch protocol scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field

from pycie.sim.network import Frame
from pycie.telemetry.events import EventType, Layer
from pycie.telemetry.packet import ensure_packet_id

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
        packet_id = ensure_packet_id(frame)
        egress_interfaces = self.lookup_egress_interfaces(ingress_if, frame.dst_mac)
        if self.should_flood(frame.dst_mac):
            self.emit_trace(
                layer=Layer.L2,
                event_type=EventType.L2_FLOOD,
                ingress_if=ingress_if,
                packet_id=packet_id,
                details={
                    "dst_mac": frame.dst_mac.lower(),
                    "egress_interfaces": list(egress_interfaces),
                },
            )
        elif egress_interfaces:
            self.emit_trace(
                layer=Layer.L2,
                event_type=EventType.L2_UNICAST_FORWARD,
                ingress_if=ingress_if,
                egress_if=egress_interfaces[0],
                packet_id=packet_id,
                details={
                    "dst_mac": frame.dst_mac.lower(),
                    "egress_interface": egress_interfaces[0],
                },
            )
        for egress_if in egress_interfaces:
            self.device.send_frame(egress_if, frame)

    def learn_source_mac(self, ingress_if: str, src_mac: str) -> None:
        """Install or refresh a source-MAC entry in the local table."""
        normalized_src = src_mac.lower()
        self.mac_table[normalized_src] = MacEntry(
            mac=normalized_src,
            interface=ingress_if,
            learned_at_ms=self.now_ms,
        )
        self.emit_trace(
            layer=Layer.L2,
            event_type=EventType.MAC_LEARN,
            ingress_if=ingress_if,
            details={
                "mac": normalized_src,
                "interface": ingress_if,
            },
        )

    def lookup_egress_interfaces(self, ingress_if: str, dst_mac: str) -> list[str]:
        """Return output interfaces for destination MAC (unicast or flood set)."""
        if self.should_flood(dst_mac):
            return sorted(if_name for if_name in self.device.interfaces if if_name != ingress_if)

        entry = self.mac_table.get(dst_mac.lower())
        if entry is None:
            return sorted(if_name for if_name in self.device.interfaces if if_name != ingress_if)
        if entry.interface == ingress_if:
            return []
        return [entry.interface]

    def age_mac_table(self) -> list[MacEntry]:
        """Expire stale MAC entries based on current simulation time."""
        expired_entries = [
            entry
            for entry in self.mac_table.values()
            if self.now_ms - entry.learned_at_ms >= self.mac_aging_ms
        ]
        for entry in expired_entries:
            del self.mac_table[entry.mac]
            self.emit_trace(
                layer=Layer.L2,
                event_type=EventType.MAC_AGE_OUT,
                details={
                    "mac": entry.mac,
                    "previous_interface": entry.interface,
                },
            )
        return expired_entries

    def should_flood(self, dst_mac: str) -> bool:
        """Return True for unknown unicast and broadcast destinations."""
        normalized_dst = dst_mac.lower()
        if normalized_dst == "ff:ff:ff:ff:ff:ff":
            return True
        return normalized_dst not in self.mac_table
