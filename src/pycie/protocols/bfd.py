"""Lab 06: simplified BFD protocol scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field

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
        # Timer scheduling intentionally omitted in scaffold baseline.

    def on_frame(self, ingress_if: str, frame: Frame) -> None:
        """Parse and process BFD control packets."""
        if isinstance(frame.payload, BFDControl):
            self.receive_control(ingress_if, frame.payload)

    def open_session(self, peer_id: str) -> BFDSession:
        """Create a local BFD session object for a peer."""
        if peer_id in self.sessions:
            return self.sessions[peer_id]

        discriminator = self.discriminator_seed + len(self.sessions) + 1
        session = BFDSession(peer_id=peer_id, local_discriminator=discriminator)
        self.sessions[peer_id] = session
        return session

    def receive_control(self, peer_id: str, packet: BFDControl) -> None:
        """Apply session state transitions on inbound control packet."""
        session = self.open_session(peer_id)
        if packet.your_discriminator != session.local_discriminator:
            return

        session.remote_discriminator = packet.my_discriminator
        session.last_rx_ms = self.now_ms if hasattr(self, "device") else 0.0
        session.required_min_rx_ms = packet.required_min_rx_ms
        session.detect_mult = packet.detect_mult

        if packet.state == "UP":
            session.state = "UP" if session.state in {"INIT", "UP"} else "INIT"
        elif packet.state == "INIT":
            session.state = "INIT"

    def transmit_control(self, peer_id: str) -> BFDControl:
        """Build an outbound BFD control packet for a peer session."""
        session = self.open_session(peer_id)
        return BFDControl(
            your_discriminator=session.remote_discriminator,
            my_discriminator=session.local_discriminator,
            state=session.state,
            desired_min_tx_ms=session.desired_min_tx_ms,
            required_min_rx_ms=session.required_min_rx_ms,
            detect_mult=session.detect_mult,
        )

    def detect_time_ms(self, peer_id: str) -> int:
        """Compute detection time for the peer session."""
        session = self.sessions[peer_id]
        return session.required_min_rx_ms * session.detect_mult

    def check_timeouts(self) -> list[str]:
        """Return peer IDs whose sessions should be declared down."""
        now_ms = self.now_ms if hasattr(self, "device") else 0.0
        expired: list[str] = []
        for peer_id, session in sorted(self.sessions.items()):
            if now_ms - session.last_rx_ms >= self.detect_time_ms(peer_id):
                session.state = "DOWN"
                expired.append(peer_id)
        return expired
