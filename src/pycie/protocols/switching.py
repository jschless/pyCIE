"""Lab 01: learning switch protocol scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field

from pycie.core.todo import student_todo
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
        student_todo("Implement learning switch forwarding pipeline")

    def learn_source_mac(self, ingress_if: str, src_mac: str) -> None:
        """Install or refresh a source-MAC entry in the local table."""
        student_todo("Implement source MAC learning")

    def lookup_egress_interfaces(self, ingress_if: str, dst_mac: str) -> list[str]:
        """Return output interfaces for destination MAC (unicast or flood set)."""
        student_todo("Implement MAC lookup and flood behavior")

    def age_mac_table(self) -> None:
        """Expire stale MAC entries based on current simulation time."""
        student_todo("Implement MAC aging")

    def should_flood(self, dst_mac: str) -> bool:
        """Return True for unknown unicast and broadcast destinations."""
        student_todo("Implement broadcast/unknown flood decision")
