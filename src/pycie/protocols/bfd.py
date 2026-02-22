"""Lab 06: simplified BFD protocol scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field

from pycie.core.todo import student_todo
from pycie.sim.network import Frame

from .base import ProtocolBase


@dataclass(frozen=True)
class BFDControl:
    your_discriminator: int
    my_discriminator: int
    state: str
    desired_min_tx_ms: int
    required_min_rx_ms: int
    detect_mult: int


@dataclass
class BFDSession:
    peer_id: str
    local_discriminator: int
    remote_discriminator: int = 0
    state: str = "DOWN"
    desired_min_tx_ms: int = 300
    required_min_rx_ms: int = 300
    detect_mult: int = 3
    last_rx_ms: float = 0.0


@dataclass
class BFDProcess(ProtocolBase):
    """Simplified single-hop asynchronous BFD process.

    Reading:
    - RFC 5880
    - RFC 5881
    """

    name: str = "bfd"
    sessions: dict[str, BFDSession] = field(default_factory=dict)
    discriminator_seed: int = 1000

    def on_start(self) -> None:
        """Initialize timers for configured sessions."""
        student_todo("Start BFD periodic control transmission")

    def on_frame(self, ingress_if: str, frame: Frame) -> None:
        """Parse and process BFD control packets."""
        student_todo("Handle inbound BFD control packet")

    def open_session(self, peer_id: str) -> BFDSession:
        """Create a local BFD session object for a peer."""
        student_todo("Create BFD session with local discriminator")

    def receive_control(self, peer_id: str, packet: BFDControl) -> None:
        """Apply session state transitions on inbound control packet."""
        student_todo("Implement BFD state machine transition logic")

    def transmit_control(self, peer_id: str) -> BFDControl:
        """Build an outbound BFD control packet for a peer session."""
        student_todo("Build outbound BFD control packet fields")

    def detect_time_ms(self, peer_id: str) -> int:
        """Compute detection time for the peer session."""
        student_todo("Compute BFD detection timer")

    def check_timeouts(self) -> list[str]:
        """Return peer IDs whose sessions should be declared down."""
        student_todo("Implement timeout detection based on last receive time")
