"""Lab 06b: TCP/UDP fundamentals in a deterministic teaching model."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from ipaddress import ip_address

from pycie.model.headers import IPv4Header, IPv6Header, TCPHeader, UDPHeader
from pycie.model.packet import PacketStack

from .base import ProtocolBase

_ALLOWED_TCP_FLAGS = {"syn", "ack", "fin", "rst", "psh", "urg"}


class TCPState(StrEnum):
    CLOSED = "closed"
    SYN_SENT = "syn_sent"
    SYN_RECEIVED = "syn_received"
    ESTABLISHED = "established"
    FIN_WAIT = "fin_wait"
    CLOSE_WAIT = "close_wait"


@dataclass(frozen=True)
class TCPSegment:
    src_port: int
    dst_port: int
    seq: int = 0
    ack: int = 0
    flags: frozenset[str] = frozenset()


@dataclass
class TCPConnection:
    """Tiny TCP state machine focused on handshake and close behavior."""

    state: "TCPState | str" = TCPState.CLOSED

    def send_syn(self, *, src_port: int, dst_port: int) -> TCPSegment:
        if self.state != TCPState.CLOSED:
            raise RuntimeError("syn_only_from_closed")
        self.state = TCPState.SYN_SENT
        return TCPSegment(src_port=src_port, dst_port=dst_port, flags=frozenset({"syn"}))

    def send_fin(self, *, src_port: int, dst_port: int) -> TCPSegment:
        if self.state != TCPState.ESTABLISHED:
            raise RuntimeError("fin_only_from_established")
        self.state = TCPState.FIN_WAIT
        return TCPSegment(src_port=src_port, dst_port=dst_port, flags=frozenset({"fin", "ack"}))

    def receive(self, segment: TCPSegment) -> str:
        if not validate_tcp_segment(segment):
            return "invalid_segment"

        flags = segment.flags
        if "rst" in flags:
            self.state = TCPState.CLOSED
            return "reset"

        if self.state == TCPState.CLOSED and flags == frozenset({"syn"}):
            self.state = TCPState.SYN_RECEIVED
            return "syn_received"

        if self.state == TCPState.SYN_SENT and flags == frozenset({"syn", "ack"}):
            self.state = TCPState.ESTABLISHED
            return "syn_ack_received"

        if self.state == TCPState.SYN_RECEIVED and flags == frozenset({"ack"}):
            self.state = TCPState.ESTABLISHED
            return "ack_received"

        if self.state == TCPState.FIN_WAIT and flags == frozenset({"ack"}):
            self.state = TCPState.CLOSED
            return "close_complete"

        if self.state == TCPState.ESTABLISHED and "fin" in flags:
            self.state = TCPState.CLOSE_WAIT
            return "fin_received"

        return "ignored"


def validate_tcp_segment(segment: TCPSegment) -> bool:
    """Validate basic TCP flag combinations for this lab model."""
    flags = segment.flags
    if not flags.issubset(_ALLOWED_TCP_FLAGS):
        return False
    if "syn" in flags and "fin" in flags:
        return False
    if "rst" in flags and ("syn" in flags or "fin" in flags):
        return False
    return True


@dataclass
class TransportFundamentalsProcess(ProtocolBase):
    """Transport helpers used by ACL, NAT, and packet construction labs."""

    name: str = "tcp_udp_fundamentals"
    sessions: dict[str, TCPConnection] = field(default_factory=dict)

    def open_session(self, session_id: str, *, src_port: int, dst_port: int) -> TCPSegment:
        """Create a session and emit SYN from closed state."""
        conn = self.sessions.setdefault(session_id, TCPConnection())
        return conn.send_syn(src_port=src_port, dst_port=dst_port)

    def close_session(self, session_id: str, *, src_port: int, dst_port: int) -> TCPSegment:
        """Initiate close by sending FIN+ACK from established state."""
        conn = self.sessions[session_id]
        return conn.send_fin(src_port=src_port, dst_port=dst_port)

    def receive_segment(self, session_id: str, segment: TCPSegment) -> str:
        """Feed inbound segment into one session state machine."""
        conn = self.sessions.setdefault(session_id, TCPConnection())
        return conn.receive(segment)

    def extract_flow_tuple(self, packet: PacketStack) -> tuple[str, str, str, int, int] | None:
        """Extract canonical 5-tuple from PacketStack when possible."""
        l3 = next(
            (
                header
                for header in packet.headers
                if isinstance(header, (IPv4Header, IPv6Header))
            ),
            None,
        )
        if l3 is None:
            return None

        for header in packet.headers:
            if isinstance(header, TCPHeader):
                return ("tcp", l3.src_ip, l3.dst_ip, header.src_port, header.dst_port)
            if isinstance(header, UDPHeader):
                return ("udp", l3.src_ip, l3.dst_ip, header.src_port, header.dst_port)
        return None

    def compute_udp_checksum(
        self,
        *,
        src_ip: str,
        dst_ip: str,
        udp_header: UDPHeader,
        payload: bytes,
    ) -> int:
        """Compute deterministic pseudo-header checksum for teaching purposes."""
        src = ip_address(src_ip).packed
        dst = ip_address(dst_ip).packed

        accumulator = 0
        accumulator += sum(src)
        accumulator += sum(dst)
        accumulator += 17  # UDP protocol number
        accumulator += udp_header.src_port
        accumulator += udp_header.dst_port
        accumulator += udp_header.length
        accumulator += sum(payload)

        checksum = (~(accumulator & 0xFFFF)) & 0xFFFF
        return checksum

    def build_udp_header(
        self,
        *,
        src_port: int,
        dst_port: int,
        payload: bytes,
        src_ip: str = "192.0.2.1",
        dst_ip: str = "198.51.100.1",
    ) -> UDPHeader:
        """Build a UDP header with computed length and checksum."""
        base = UDPHeader(src_port=src_port, dst_port=dst_port, length=8 + len(payload), checksum=0)
        checksum = self.compute_udp_checksum(
            src_ip=src_ip,
            dst_ip=dst_ip,
            udp_header=base,
            payload=payload,
        )
        return UDPHeader(src_port=src_port, dst_port=dst_port, length=base.length, checksum=checksum)
