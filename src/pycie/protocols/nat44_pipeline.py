"""Lab 21: NAT44 SNAT/DNAT/PAT forwarding pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from ipaddress import ip_address, ip_network

from pycie.model.headers import IPv4Header
from pycie.model.packet import PacketStack

from .base import ProtocolBase


@dataclass(frozen=True)
class NAT44StaticRule:
    public_ip: str
    public_port: int
    inside_ip: str
    inside_port: int
    protocol: str


@dataclass(frozen=True)
class NAT44Session:
    inside_ip: str
    inside_port: int
    outside_ip: str
    outside_port: int
    translated_ip: str
    translated_port: int
    protocol: str
    created_at_ms: int
    last_seen_ms: int


@dataclass
class NAT44Pipeline(ProtocolBase):
    """Deterministic stateful NAT44 translation pipeline."""

    name: str = "nat44_pipeline"
    inside_prefix: str = "10.0.0.0/8"
    outside_prefix: str = "0.0.0.0/0"
    public_ip: str = "203.0.113.1"
    port_min: int = 10_000
    port_max: int = 20_000
    session_timeout_ms: int = 300_000
    sessions: dict[tuple[str, int, str, int, str], NAT44Session] = field(default_factory=dict)
    static_rules: list[NAT44StaticRule] = field(default_factory=list)

    def install_static_rule(self, rule: NAT44StaticRule) -> None:
        self.static_rules.append(rule)

    def translate_outbound(self, packet: PacketStack, *, now_ms: int) -> tuple[PacketStack | None, str | None]:
        """Apply outbound SNAT/PAT for inside-to-outside traffic."""
        ipv4 = _find_ipv4(packet)
        if ipv4 is None:
            return None, "no_ipv4_header"
        if not _in_prefix(ipv4.src_ip, self.inside_prefix):
            return packet.clone(), None

        l4 = _read_l4_tuple(packet)
        if l4 is None:
            return None, "missing_l4_tuple"
        protocol, src_port, dst_port = l4

        key = (ipv4.src_ip, src_port, ipv4.dst_ip, dst_port, protocol)
        session = self.sessions.get(key)
        if session is None:
            translated_port = self._allocate_port()
            if translated_port is None:
                return None, "nat_pool_exhausted"
            session = NAT44Session(
                inside_ip=ipv4.src_ip,
                inside_port=src_port,
                outside_ip=ipv4.dst_ip,
                outside_port=dst_port,
                translated_ip=self.public_ip,
                translated_port=translated_port,
                protocol=protocol,
                created_at_ms=now_ms,
                last_seen_ms=now_ms,
            )
            self.sessions[key] = session
        else:
            self.sessions[key] = _touch_session(session, now_ms=now_ms)
            session = self.sessions[key]

        translated = packet.clone()
        _replace_ipv4(translated, src_ip=session.translated_ip, dst_ip=ipv4.dst_ip)
        translated.metadata["src_port"] = session.translated_port
        translated.metadata["dst_port"] = dst_port
        translated.metadata["nat_direction"] = "outbound"
        translated.metadata["nat_session_key"] = key
        return translated, None

    def translate_inbound(self, packet: PacketStack, *, now_ms: int) -> tuple[PacketStack | None, str | None]:
        """Apply inbound DNAT for static rules and dynamic session return flows."""
        ipv4 = _find_ipv4(packet)
        if ipv4 is None:
            return None, "no_ipv4_header"
        l4 = _read_l4_tuple(packet)
        if l4 is None:
            return None, "missing_l4_tuple"
        protocol, src_port, dst_port = l4

        for rule in self.static_rules:
            if (
                ipv4.dst_ip == rule.public_ip
                and dst_port == rule.public_port
                and protocol == rule.protocol
            ):
                translated = packet.clone()
                _replace_ipv4(translated, src_ip=ipv4.src_ip, dst_ip=rule.inside_ip)
                translated.metadata["src_port"] = src_port
                translated.metadata["dst_port"] = rule.inside_port
                translated.metadata["nat_direction"] = "inbound_static"
                return translated, None

        session = self._find_session_by_translated(protocol=protocol, translated_port=dst_port)
        if session is None:
            return None, "session_not_found"
        if ipv4.dst_ip != session.translated_ip:
            return None, "translated_ip_mismatch"
        if ipv4.src_ip != session.outside_ip or src_port != session.outside_port:
            return None, "return_path_mismatch"

        self._update_session(session, now_ms=now_ms)
        translated = packet.clone()
        _replace_ipv4(translated, src_ip=ipv4.src_ip, dst_ip=session.inside_ip)
        translated.metadata["src_port"] = src_port
        translated.metadata["dst_port"] = session.inside_port
        translated.metadata["nat_direction"] = "inbound_dynamic"
        return translated, None

    def age_sessions(self, *, now_ms: int) -> None:
        expired = [
            key
            for key, session in self.sessions.items()
            if now_ms - session.last_seen_ms >= self.session_timeout_ms
        ]
        for key in expired:
            del self.sessions[key]

    def _allocate_port(self) -> int | None:
        used = {session.translated_port for session in self.sessions.values()}
        for port in range(self.port_min, self.port_max + 1):
            if port not in used:
                return port
        return None

    def _find_session_by_translated(self, *, protocol: str, translated_port: int) -> NAT44Session | None:
        candidates = [
            session
            for session in self.sessions.values()
            if session.protocol == protocol and session.translated_port == translated_port
        ]
        if not candidates:
            return None
        return sorted(
            candidates,
            key=lambda session: (
                session.created_at_ms,
                session.inside_ip,
                session.inside_port,
                session.outside_ip,
                session.outside_port,
            ),
        )[0]

    def _update_session(self, target: NAT44Session, *, now_ms: int) -> None:
        for key, session in list(self.sessions.items()):
            if session == target:
                self.sessions[key] = _touch_session(session, now_ms=now_ms)
                return


def _find_ipv4(packet: PacketStack) -> IPv4Header | None:
    return next((header for header in packet.headers if isinstance(header, IPv4Header)), None)


def _replace_ipv4(packet: PacketStack, *, src_ip: str, dst_ip: str) -> None:
    for idx, header in enumerate(packet.headers):
        if isinstance(header, IPv4Header):
            packet.headers[idx] = IPv4Header(
                src_ip=src_ip,
                dst_ip=dst_ip,
                ttl=header.ttl,
                dscp=header.dscp,
                protocol=header.protocol,
            )
            return


def _read_l4_tuple(packet: PacketStack) -> tuple[str, int, int] | None:
    protocol = packet.metadata.get("l4_proto")
    src_port = packet.metadata.get("src_port")
    dst_port = packet.metadata.get("dst_port")
    if not isinstance(protocol, str) or not isinstance(src_port, int) or not isinstance(dst_port, int):
        return None
    return protocol, src_port, dst_port


def _touch_session(session: NAT44Session, *, now_ms: int) -> NAT44Session:
    return NAT44Session(
        inside_ip=session.inside_ip,
        inside_port=session.inside_port,
        outside_ip=session.outside_ip,
        outside_port=session.outside_port,
        translated_ip=session.translated_ip,
        translated_port=session.translated_port,
        protocol=session.protocol,
        created_at_ms=session.created_at_ms,
        last_seen_ms=now_ms,
    )


def _in_prefix(ip: str, prefix: str) -> bool:
    return ip_address(ip) in ip_network(prefix, strict=False)
