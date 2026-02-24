"""Lab 22: ICMP/ICMPv6 echo and control-plane error helpers."""

from __future__ import annotations

from dataclasses import dataclass

from pycie.model.headers import ICMPHeader, ICMPv6Header, IPv4Header, IPv6Header, UDPHeader
from pycie.model.packet import PacketStack

from .base import ProtocolBase

ICMP_ECHO_REPLY = 0
ICMP_DESTINATION_UNREACHABLE = 3
ICMP_ECHO_REQUEST = 8
ICMP_TIME_EXCEEDED = 11

ICMPV6_DESTINATION_UNREACHABLE = 1
ICMPV6_TIME_EXCEEDED = 3
ICMPV6_ECHO_REQUEST = 128
ICMPV6_ECHO_REPLY = 129


@dataclass(frozen=True)
class TracerouteHopResult:
    hop_index: int
    responder_ip: str
    outcome: str
    icmp_type: int
    icmp_code: int


@dataclass
class ICMPControlPlaneProcess(ProtocolBase):
    """Construct ICMP probes/replies and deterministic traceroute outcomes."""

    name: str = "icmp_control_plane_basics"

    def build_echo_request(
        self,
        *,
        src_ip: str,
        dst_ip: str,
        ipv6: bool = False,
        identifier: int = 1,
        sequence: int = 1,
        payload: bytes = b"",
    ) -> PacketStack:
        """Build ICMP echo request for IPv4 or IPv6."""
        if ipv6:
            return PacketStack(
                headers=[
                    IPv6Header(src_ip=src_ip, dst_ip=dst_ip, hop_limit=64, next_header=58),
                    ICMPv6Header(
                        icmp_type=ICMPV6_ECHO_REQUEST,
                        icmp_code=0,
                        identifier=identifier,
                        sequence=sequence,
                    ),
                ],
                payload=payload,
            )

        return PacketStack(
            headers=[
                IPv4Header(src_ip=src_ip, dst_ip=dst_ip, ttl=64, protocol=1),
                ICMPHeader(
                    icmp_type=ICMP_ECHO_REQUEST,
                    icmp_code=0,
                    identifier=identifier,
                    sequence=sequence,
                ),
            ],
            payload=payload,
        )

    def build_echo_reply(self, request: PacketStack, *, responder_ip: str | None = None) -> PacketStack:
        """Generate echo reply by swapping source/destination from request."""
        if _is_ipv6(request):
            ip_header = _find_header(request, IPv6Header)
            if ip_header is None:
                raise ValueError("missing_ipv6_header")
            icmp_header = _find_header(request, ICMPv6Header)
            if icmp_header is None or icmp_header.icmp_type != ICMPV6_ECHO_REQUEST:
                raise ValueError("not_icmpv6_echo_request")
            src_ip = responder_ip or ip_header.dst_ip
            return PacketStack(
                headers=[
                    IPv6Header(src_ip=src_ip, dst_ip=ip_header.src_ip, hop_limit=64, next_header=58),
                    ICMPv6Header(
                        icmp_type=ICMPV6_ECHO_REPLY,
                        icmp_code=0,
                        identifier=icmp_header.identifier,
                        sequence=icmp_header.sequence,
                    ),
                ],
                payload=request.payload,
            )

        ip_header = _find_header(request, IPv4Header)
        if ip_header is None:
            raise ValueError("missing_ipv4_header")
        icmp_header = _find_header(request, ICMPHeader)
        if icmp_header is None or icmp_header.icmp_type != ICMP_ECHO_REQUEST:
            raise ValueError("not_icmp_echo_request")
        src_ip = responder_ip or ip_header.dst_ip
        return PacketStack(
            headers=[
                IPv4Header(src_ip=src_ip, dst_ip=ip_header.src_ip, ttl=64, protocol=1),
                ICMPHeader(
                    icmp_type=ICMP_ECHO_REPLY,
                    icmp_code=0,
                    identifier=icmp_header.identifier,
                    sequence=icmp_header.sequence,
                ),
            ],
            payload=request.payload,
        )

    def build_time_exceeded(
        self,
        packet: PacketStack,
        *,
        responder_ip: str,
        ipv6: bool | None = None,
    ) -> PacketStack:
        """Build time-exceeded response for TTL/hop-limit expiry."""
        use_ipv6 = _is_ipv6(packet) if ipv6 is None else ipv6
        if use_ipv6:
            ip_header = _find_header(packet, IPv6Header)
            if ip_header is None:
                raise ValueError("missing_ipv6_header")
            return PacketStack(
                headers=[
                    IPv6Header(src_ip=responder_ip, dst_ip=ip_header.src_ip, hop_limit=64, next_header=58),
                    ICMPv6Header(icmp_type=ICMPV6_TIME_EXCEEDED, icmp_code=0),
                ],
                payload=packet.payload,
            )

        ip_header = _find_header(packet, IPv4Header)
        if ip_header is None:
            raise ValueError("missing_ipv4_header")
        return PacketStack(
            headers=[
                IPv4Header(src_ip=responder_ip, dst_ip=ip_header.src_ip, ttl=64, protocol=1),
                ICMPHeader(icmp_type=ICMP_TIME_EXCEEDED, icmp_code=0),
            ],
            payload=packet.payload,
        )

    def build_destination_unreachable(
        self,
        packet: PacketStack,
        *,
        responder_ip: str,
        code: int = 0,
        ipv6: bool | None = None,
    ) -> PacketStack:
        """Build destination-unreachable response for IPv4 or IPv6."""
        use_ipv6 = _is_ipv6(packet) if ipv6 is None else ipv6
        if use_ipv6:
            ip_header = _find_header(packet, IPv6Header)
            if ip_header is None:
                raise ValueError("missing_ipv6_header")
            return PacketStack(
                headers=[
                    IPv6Header(src_ip=responder_ip, dst_ip=ip_header.src_ip, hop_limit=64, next_header=58),
                    ICMPv6Header(icmp_type=ICMPV6_DESTINATION_UNREACHABLE, icmp_code=code),
                ],
                payload=packet.payload,
            )

        ip_header = _find_header(packet, IPv4Header)
        if ip_header is None:
            raise ValueError("missing_ipv4_header")
        return PacketStack(
            headers=[
                IPv4Header(src_ip=responder_ip, dst_ip=ip_header.src_ip, ttl=64, protocol=1),
                ICMPHeader(icmp_type=ICMP_DESTINATION_UNREACHABLE, icmp_code=code),
            ],
            payload=packet.payload,
        )

    def traceroute_probe(
        self,
        *,
        src_ip: str,
        dst_ip: str,
        ttl: int,
        ipv6: bool = False,
        base_port: int = 33_434,
    ) -> PacketStack:
        """Build UDP traceroute probe packet with explicit hop budget."""
        if ttl <= 0:
            raise ValueError("ttl_must_be_positive")

        if ipv6:
            return PacketStack(
                headers=[
                    IPv6Header(src_ip=src_ip, dst_ip=dst_ip, hop_limit=ttl, next_header=17),
                    UDPHeader(src_port=49_152 + ttl, dst_port=base_port + ttl, length=8),
                ],
                payload=b"",
            )

        return PacketStack(
            headers=[
                IPv4Header(src_ip=src_ip, dst_ip=dst_ip, ttl=ttl, protocol=17),
                UDPHeader(src_port=49_152 + ttl, dst_port=base_port + ttl, length=8),
            ],
            payload=b"",
        )

    def traceroute_hop_result(
        self,
        probe: PacketStack,
        *,
        hop_index: int,
        destination_hop: int,
        responder_ip: str,
    ) -> TracerouteHopResult:
        """Return deterministic traceroute outcome for one hop index."""
        if hop_index <= 0:
            raise ValueError("hop_index_must_be_positive")
        if destination_hop <= 0:
            raise ValueError("destination_hop_must_be_positive")

        if hop_index < destination_hop:
            if _is_ipv6(probe):
                return TracerouteHopResult(
                    hop_index=hop_index,
                    responder_ip=responder_ip,
                    outcome="time_exceeded",
                    icmp_type=ICMPV6_TIME_EXCEEDED,
                    icmp_code=0,
                )
            return TracerouteHopResult(
                hop_index=hop_index,
                responder_ip=responder_ip,
                outcome="time_exceeded",
                icmp_type=ICMP_TIME_EXCEEDED,
                icmp_code=0,
            )

        if _is_ipv6(probe):
            return TracerouteHopResult(
                hop_index=hop_index,
                responder_ip=responder_ip,
                outcome="destination_reached",
                icmp_type=ICMPV6_ECHO_REPLY,
                icmp_code=0,
            )
        return TracerouteHopResult(
            hop_index=hop_index,
            responder_ip=responder_ip,
            outcome="destination_reached",
            icmp_type=ICMP_ECHO_REPLY,
            icmp_code=0,
        )


def _is_ipv6(packet: PacketStack) -> bool:
    return any(isinstance(header, IPv6Header) for header in packet.headers)


def _find_header(
    packet: PacketStack,
    header_type: type[IPv4Header] | type[IPv6Header] | type[ICMPHeader] | type[ICMPv6Header],
) -> IPv4Header | IPv6Header | ICMPHeader | ICMPv6Header | None:
    return next((header for header in packet.headers if isinstance(header, header_type)), None)
