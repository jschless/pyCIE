"""Lab 17: BGP FSM and transport lifecycle model."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from pycie.sim.network import Frame

from .base import ProtocolBase


class BGPFSMState(StrEnum):
    IDLE = "IDLE"
    CONNECT = "CONNECT"
    OPENSENT = "OPENSENT"
    OPENCONFIRM = "OPENCONFIRM"
    ESTABLISHED = "ESTABLISHED"


@dataclass(frozen=True)
class BGPTransportOpen:
    asn: int
    router_id: str
    hold_time_s: int


@dataclass(frozen=True)
class BGPTransportKeepalive:
    pass


@dataclass(frozen=True)
class BGPTransportUpdate:
    prefix: str
    next_hop: str
    withdraw: bool = False


@dataclass(frozen=True)
class BGPTransportNotification:
    code: int
    subcode: int
    reason: str


@dataclass
class BGPTransportSession:
    """Deterministic BGP transport/FSM session model for one peer."""

    peer_id: str
    peer_as: int
    local_as: int
    local_router_id: str
    configured_hold_time_s: int = 90
    state: "BGPFSMState | str" = BGPFSMState.IDLE
    negotiated_hold_time_s: int = 90
    keepalive_interval_s: int = 30
    hold_timer_s: int = 0
    keepalive_timer_s: int = 0
    adj_rib_in: dict[str, BGPTransportUpdate] = field(default_factory=dict)
    last_error: str | None = None

    def start(self) -> None:
        """Start BGP FSM from IDLE."""
        if self.state == BGPFSMState.IDLE:
            self.state = BGPFSMState.CONNECT

    def on_tcp_up(self) -> BGPTransportOpen | None:
        """Handle transport establishment and emit OPEN."""
        if self.state != BGPFSMState.CONNECT:
            return None
        self.state = BGPFSMState.OPENSENT
        self._reset_timers()
        return BGPTransportOpen(
            asn=self.local_as,
            router_id=self.local_router_id,
            hold_time_s=self.configured_hold_time_s,
        )

    def on_tcp_down(self, *, reason: str = "tcp_down") -> None:
        """Reset session state on transport down."""
        self._reset_session(reason=reason)

    def receive_open(self, message: BGPTransportOpen) -> BGPTransportKeepalive | BGPTransportNotification:
        """Validate OPEN and move to OPENCONFIRM."""
        if self.state not in {BGPFSMState.OPENSENT, BGPFSMState.OPENCONFIRM}:
            return self._reset_with_notification(code=5, subcode=0, reason="fsm_state_violation_open")
        if message.asn != self.peer_as:
            return self._reset_with_notification(code=2, subcode=2, reason="peer_as_mismatch")
        if message.hold_time_s < 3:
            return self._reset_with_notification(code=2, subcode=6, reason="unacceptable_hold_time")

        self.negotiated_hold_time_s = min(self.configured_hold_time_s, message.hold_time_s)
        self.keepalive_interval_s = max(1, self.negotiated_hold_time_s // 3)
        self.state = BGPFSMState.OPENCONFIRM
        self._reset_timers()
        return BGPTransportKeepalive()

    def receive_keepalive(self) -> bool:
        """Handle KEEPALIVE and advance/refresh hold timer."""
        if self.state == BGPFSMState.OPENCONFIRM:
            self.state = BGPFSMState.ESTABLISHED
            self.hold_timer_s = 0
            self.keepalive_timer_s = 0
            return True
        if self.state == BGPFSMState.ESTABLISHED:
            self.hold_timer_s = 0
            return True
        return False

    def receive_update(self, message: BGPTransportUpdate) -> BGPTransportNotification | None:
        """Install UPDATE in Adj-RIB-In or reset on malformed state/payload."""
        if self.state != BGPFSMState.ESTABLISHED:
            return self._reset_with_notification(code=5, subcode=0, reason="update_before_established")
        if not _valid_prefix(message.prefix):
            return self._reset_with_notification(code=3, subcode=10, reason="malformed_prefix")
        if not message.withdraw and not message.next_hop:
            return self._reset_with_notification(code=3, subcode=8, reason="missing_next_hop")

        self.hold_timer_s = 0
        if message.withdraw:
            self.adj_rib_in.pop(message.prefix, None)
        else:
            self.adj_rib_in[message.prefix] = message
        return None

    def receive_notification(self, message: BGPTransportNotification) -> None:
        """Handle received NOTIFICATION by resetting session."""
        self._reset_session(reason=f"notification:{message.reason}")

    def inject_malformed_message(self, *, reason: str = "malformed_message") -> BGPTransportNotification:
        """Force notification + reset (test/helper hook)."""
        return self._reset_with_notification(code=3, subcode=0, reason=reason)

    def tick(self, elapsed_s: int) -> list[object]:
        """Advance hold/keepalive timers and emit periodic keepalives."""
        outbound: list[object] = []
        if elapsed_s <= 0:
            return outbound
        if self.state in {BGPFSMState.IDLE, BGPFSMState.CONNECT}:
            return outbound

        self.hold_timer_s += elapsed_s
        if self.state == BGPFSMState.ESTABLISHED:
            self.keepalive_timer_s += elapsed_s
            while self.keepalive_timer_s >= self.keepalive_interval_s:
                outbound.append(BGPTransportKeepalive())
                self.keepalive_timer_s -= self.keepalive_interval_s

        if self.hold_timer_s >= self.negotiated_hold_time_s:
            self._reset_session(reason="hold_timer_expired")
        return outbound

    def _reset_timers(self) -> None:
        self.hold_timer_s = 0
        self.keepalive_timer_s = 0

    def _reset_session(self, *, reason: str) -> None:
        self.state = BGPFSMState.IDLE
        self._reset_timers()
        self.last_error = reason
        self.adj_rib_in = {}

    def _reset_with_notification(self, *, code: int, subcode: int, reason: str) -> BGPTransportNotification:
        notification = BGPTransportNotification(code=code, subcode=subcode, reason=reason)
        self._reset_session(reason=f"notification_sent:{reason}")
        return notification


@dataclass
class BGPTransportProcess(ProtocolBase):
    """BGP transport process that dispatches session-level FSM logic."""

    name: str = "bgp_fsm_transport"
    sessions: dict[str, BGPTransportSession] = field(default_factory=dict)

    def on_start(self) -> None:
        for session in self.sessions.values():
            session.start()

    def on_frame(self, ingress_if: str, frame: Frame) -> None:
        del ingress_if
        payload = frame.payload
        session = self.sessions.get(frame.src_mac)
        if session is None:
            return
        if isinstance(payload, BGPTransportOpen):
            session.receive_open(payload)
        elif isinstance(payload, BGPTransportKeepalive):
            session.receive_keepalive()
        elif isinstance(payload, BGPTransportUpdate):
            session.receive_update(payload)
        elif isinstance(payload, BGPTransportNotification):
            session.receive_notification(payload)

    def on_tick(self) -> None:
        for session in self.sessions.values():
            session.tick(1)


def _valid_prefix(prefix: str) -> bool:
    if "/" not in prefix:
        return False
    network, length = prefix.split("/", 1)
    if not network or not length:
        return False
    if not length.isdigit():
        return False
    value = int(length)
    return 0 <= value <= 32
