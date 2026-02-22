"""Lab 05: simplified LDP protocol scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field

from pycie.core.todo import student_todo
from pycie.sim.network import Frame

from .base import ProtocolBase


@dataclass(frozen=True)
class LDPHello:
    router_id: str


@dataclass(frozen=True)
class LabelMapping:
    prefix: str
    label: int
    next_hop: str


@dataclass
class LDPNeighbor:
    router_id: str
    state: str = "DOWN"


@dataclass
class LDPProcess(ProtocolBase):
    """Simplified downstream-unsolicited LDP process.

    Reading:
    - RFC 5036
    - RFC 3031 (MPLS architecture)
    """

    name: str = "ldp"
    router_id: str = "0.0.0.0"
    neighbors: dict[str, LDPNeighbor] = field(default_factory=dict)
    lib: dict[str, int] = field(default_factory=dict)
    remote_bindings: dict[str, dict[str, int]] = field(default_factory=dict)
    label_counter: int = 16

    def on_start(self) -> None:
        """Send discovery hellos and advertise initial local bindings."""
        student_todo("Start LDP discovery and mapping advertisement")

    def on_frame(self, ingress_if: str, frame: Frame) -> None:
        """Handle hello and label mapping messages."""
        student_todo("Parse and process inbound LDP messages")

    def allocate_local_label(self, prefix: str) -> int:
        """Allocate (or return existing) local label for prefix."""
        student_todo("Implement local label allocation policy")

    def advertise_bindings(self) -> list[LabelMapping]:
        """Build current outbound label mapping set."""
        student_todo("Build outbound label mapping advertisements")

    def process_label_mapping(self, peer_id: str, mapping: LabelMapping) -> None:
        """Store peer binding and trigger LFIB update."""
        student_todo("Install remote label binding and update forwarding view")

    def build_lfib(self) -> dict[str, tuple[int, int | None]]:
        """Return prefix -> (out_label, in_label_or_none) mapping."""
        student_todo("Compute LFIB from local and remote bindings")
