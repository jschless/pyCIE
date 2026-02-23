"""Lab 20: IPv6 forwarding with Neighbor Discovery cache behavior."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from ipaddress import IPv6Address, IPv6Network, ip_address, ip_network

from pycie.model.headers import IPv6Header
from pycie.model.packet import PacketStack

from .base import ProtocolBase


@dataclass(frozen=True)
class IPv6Route:
    prefix: str
    next_hop: str | None
    outgoing_interface: str
    metric: int = 0


@dataclass(frozen=True)
class NDEntry:
    ip: str
    mac: str
    learned_at_ms: int
    ttl_ms: int = 1_200_000


@dataclass(frozen=True)
class PendingNDPacket:
    next_hop_ip: str
    packet: PacketStack
    enqueued_at_ms: int


@dataclass(frozen=True)
class NDNeighborSolicitation:
    target_ip: str
    source_ip: str


@dataclass(frozen=True)
class NDNeighborAdvertisement:
    target_ip: str
    target_mac: str


@dataclass
class IPv6NDForwarder(ProtocolBase):
    """Deterministic IPv6 route + ND forwarding pipeline."""

    name: str = "ipv6_nd_forwarding"
    routes: list[IPv6Route] = field(default_factory=list)
    neighbors: dict[str, NDEntry] = field(default_factory=dict)
    pending: dict[str, list[PendingNDPacket]] = field(default_factory=dict)

    def install_route(self, route: IPv6Route) -> None:
        self.routes.append(route)

    def learn_neighbor(self, ip: str, mac: str, *, now_ms: int, ttl_ms: int = 1_200_000) -> None:
        self.neighbors[ip] = NDEntry(ip=ip, mac=mac, learned_at_ms=now_ms, ttl_ms=ttl_ms)

    def age_neighbors(self, *, now_ms: int) -> None:
        expired = [
            ip
            for ip, entry in self.neighbors.items()
            if now_ms - entry.learned_at_ms >= entry.ttl_ms
        ]
        for ip in expired:
            del self.neighbors[ip]

    def lookup_route(self, dst_ip: str) -> IPv6Route | None:
        dst = ip_address(dst_ip)
        candidates = [
            route
            for route in self.routes
            if dst in ip_network(route.prefix, strict=False)
        ]
        if not candidates:
            return None
        return sorted(
            candidates,
            key=lambda route: (
                -ip_network(route.prefix, strict=False).prefixlen,
                route.metric,
                route.outgoing_interface,
                "" if route.next_hop is None else route.next_hop,
            ),
        )[0]

    def queue_pending(self, next_hop_ip: str, packet: PacketStack, *, now_ms: int) -> None:
        self.pending.setdefault(next_hop_ip, []).append(
            PendingNDPacket(next_hop_ip=next_hop_ip, packet=packet.clone(), enqueued_at_ms=now_ms)
        )

    def resolve_neighbor(self, advertisement: NDNeighborAdvertisement, *, now_ms: int) -> list[PacketStack]:
        self.learn_neighbor(advertisement.target_ip, advertisement.target_mac, now_ms=now_ms)
        queued = self.pending.pop(advertisement.target_ip, [])
        forwarded: list[PacketStack] = []
        for pending in queued:
            updated = decrement_hop_limit(pending.packet)
            if updated is not None:
                forwarded.append(updated)
        return forwarded

    def forward(self, packet: PacketStack, *, now_ms: int) -> tuple[str | None, PacketStack | None, str | None]:
        self.age_neighbors(now_ms=now_ms)
        ipv6_header = next((header for header in packet.headers if isinstance(header, IPv6Header)), None)
        if ipv6_header is None:
            return None, None, "no_ipv6_header"
        if ipv6_header.hop_limit <= 1:
            return None, None, "hop_limit_expired"

        route = self.lookup_route(ipv6_header.dst_ip)
        if route is None:
            return None, None, "no_route"

        next_hop_ip = route.next_hop or ipv6_header.dst_ip
        nd_entry = self.neighbors.get(next_hop_ip)
        if nd_entry is None:
            self.queue_pending(next_hop_ip, packet, now_ms=now_ms)
            return None, None, "neighbor_unresolved"

        forwarded = decrement_hop_limit(packet)
        if forwarded is None:
            return None, None, "hop_limit_expired"
        forwarded.metadata["resolved_neighbor_mac"] = nd_entry.mac
        forwarded.metadata["resolved_neighbor_ip"] = next_hop_ip
        return route.outgoing_interface, forwarded, None

    def should_solicit(self, target_ip: str) -> bool:
        return target_ip not in self.neighbors


def decrement_hop_limit(packet: PacketStack) -> PacketStack | None:
    updated = packet.clone()
    for index, header in enumerate(updated.headers):
        if isinstance(header, IPv6Header):
            if header.hop_limit <= 1:
                return None
            updated.headers[index] = replace(header, hop_limit=header.hop_limit - 1)
            return updated
    return None


def normalize_ipv6(ip: str) -> str:
    return str(IPv6Address(ip))


def prefix_contains(prefix: str, ip: str) -> bool:
    return ip_address(ip) in IPv6Network(prefix, strict=False)
