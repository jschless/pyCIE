"""Lab 02: simplified spanning tree protocol scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field

from pycie.core.todo import student_todo
from pycie.sim.network import Frame

from .base import ProtocolBase


@dataclass(frozen=True, order=True)
class BridgeId:
    priority: int
    mac: str


@dataclass(frozen=True)
class BPDU:
    root_id: BridgeId
    root_path_cost: int
    bridge_id: BridgeId
    port_id: int
    hello_time_ms: int = 2_000
    max_age_ms: int = 20_000


@dataclass
class STPPort:
    if_name: str
    port_id: int
    path_cost: int = 4
    role: str = "DESIGNATED"
    state: str = "FORWARDING"


@dataclass
class STPProcess(ProtocolBase):
    """Simplified 802.1D-style spanning tree process.

    Reading:
    - IEEE 802.1D bridge protocol and BPDU ordering
    """

    name: str = "stp"
    bridge_priority: int = 32768
    bridge_mac: str = "00:00:00:00:00:00"
    ports: dict[str, STPPort] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.bridge_id = BridgeId(self.bridge_priority, self.bridge_mac)
        self.root_id = self.bridge_id
        self.root_cost = 0
        self.root_port: str | None = None

    def on_start(self) -> None:
        """Initialize local state and transmit initial BPDUs."""
        student_todo("Send initial BPDUs and bootstrap STP state")

    def on_frame(self, ingress_if: str, frame: Frame) -> None:
        """Process incoming BPDU frames only."""
        student_todo("Parse and process inbound BPDUs")

    def build_bpdu(self, egress_if: str) -> BPDU:
        """Build the BPDU announced on a given port."""
        student_todo("Build outbound BPDU based on current root view")

    def process_bpdu(self, ingress_if: str, bpdu: BPDU) -> None:
        """Update root selection and port roles from an inbound BPDU."""
        student_todo("Implement BPDU comparison and root/port selection")

    def recompute_port_states(self) -> None:
        """Set each port role/state after root calculation."""
        student_todo("Recompute DESIGNATED/ROOT/BLOCKING decisions")

    def should_forward_data(self, if_name: str) -> bool:
        """Return True if the port is in a forwarding state."""
        student_todo("Implement STP forwarding-state check")
