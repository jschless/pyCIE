"""Lab 06: simplified BFD protocol scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from pycie.sim.network import Frame
from pycie.telemetry.events import EventType, Layer

from .base import ProtocolBase


class BFDState(StrEnum):
    DOWN = "DOWN"
    INIT = "INIT"
    UP = "UP"


@dataclass(frozen=True)
class BFDControl:
    your_discriminator: int
    my_discriminator: int
    state: "BFDState | str"
    desired_min_tx_ms: int
    required_min_rx_ms: int
    detect_mult: int


@dataclass
class BFDSession:
    peer_id: str
    local_discriminator: int
    remote_discriminator: int = 0
    state: "BFDState | str" = BFDState.DOWN
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
        self.emit_trace(
            layer=Layer.L3,
            event_type=EventType.BFD_STATE_CHANGE,
            details={
                "peer_id": peer_id,
                "old_state": None,
                "new_state": BFDState.DOWN.value,
                "reason": "session_opened",
                "local_discriminator": discriminator,
            },
        )
        return session

    def receive_control(self, peer_id: str, packet: BFDControl) -> None:
        """Apply session state transitions on inbound control packet."""
        session = self.open_session(peer_id)
        old_state = BFDState(session.state)
        if packet.your_discriminator != session.local_discriminator:
            self.emit_trace(
                layer=Layer.L3,
                event_type=EventType.BFD_CONTROL_RX,
                details={
                    "peer_id": peer_id,
                    "result": "discriminator_mismatch",
                    "expected_your_discriminator": session.local_discriminator,
                    "received_your_discriminator": packet.your_discriminator,
                    "my_discriminator": packet.my_discriminator,
                    "state": BFDState(packet.state).value,
                },
            )
            return

        session.remote_discriminator = packet.my_discriminator
        session.last_rx_ms = self.now_ms if hasattr(self, "device") else 0.0
        session.required_min_rx_ms = packet.required_min_rx_ms
        session.detect_mult = packet.detect_mult

        packet_state = BFDState(packet.state)
        session_state = BFDState(session.state)
        if packet_state == BFDState.UP:
            session.state = (
                BFDState.UP
                if session_state in {BFDState.INIT, BFDState.UP}
                else BFDState.INIT
            )
        elif packet_state == BFDState.INIT:
            session.state = BFDState.INIT
        new_state = BFDState(session.state)
        self.emit_trace(
            layer=Layer.L3,
            event_type=EventType.BFD_CONTROL_RX,
            details={
                "peer_id": peer_id,
                "result": "accepted",
                "my_discriminator": packet.my_discriminator,
                "your_discriminator": packet.your_discriminator,
                "packet_state": packet_state.value,
                "old_state": old_state.value,
                "new_state": new_state.value,
            },
        )
        if old_state != new_state:
            self.emit_trace(
                layer=Layer.L3,
                event_type=EventType.BFD_STATE_CHANGE,
                details={
                    "peer_id": peer_id,
                    "old_state": old_state.value,
                    "new_state": new_state.value,
                    "reason": f"rx_{packet_state.value.lower()}",
                },
            )

    def transmit_control(self, peer_id: str) -> BFDControl:
        """Build an outbound BFD control packet for a peer session."""
        session = self.open_session(peer_id)
        control = BFDControl(
            your_discriminator=session.remote_discriminator,
            my_discriminator=session.local_discriminator,
            state=session.state,
            desired_min_tx_ms=session.desired_min_tx_ms,
            required_min_rx_ms=session.required_min_rx_ms,
            detect_mult=session.detect_mult,
        )
        self.emit_trace(
            layer=Layer.L3,
            event_type=EventType.BFD_CONTROL_TX,
            details={
                "peer_id": peer_id,
                "my_discriminator": control.my_discriminator,
                "your_discriminator": control.your_discriminator,
                "state": BFDState(control.state).value,
                "desired_min_tx_ms": control.desired_min_tx_ms,
                "required_min_rx_ms": control.required_min_rx_ms,
                "detect_mult": control.detect_mult,
            },
        )
        return control

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
                old_state = BFDState(session.state)
                session.state = BFDState.DOWN
                expired.append(peer_id)
                self.emit_trace(
                    layer=Layer.L3,
                    event_type=EventType.BFD_TIMEOUT,
                    details={
                        "peer_id": peer_id,
                        "elapsed_ms": now_ms - session.last_rx_ms,
                        "detect_time_ms": self.detect_time_ms(peer_id),
                    },
                )
                if old_state != BFDState.DOWN:
                    self.emit_trace(
                        layer=Layer.L3,
                        event_type=EventType.BFD_STATE_CHANGE,
                        details={
                            "peer_id": peer_id,
                            "old_state": old_state.value,
                            "new_state": BFDState.DOWN.value,
                            "reason": "timeout",
                        },
                    )
        return expired
