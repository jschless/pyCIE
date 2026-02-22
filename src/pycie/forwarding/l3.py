"""IPv4 forwarding pipeline scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from ipaddress import ip_address, ip_network
from typing import Literal

from pycie.model.headers import IPv4Header
from pycie.model.packet import PacketStack

L3RouteType = Literal["connected", "static", "ospf", "bgp", "ldp"]


@dataclass(frozen=True)
class L3Route:
    prefix: str
    next_hop: str | None
    outgoing_interface: str | None
    route_type: L3RouteType
    admin_distance: int
    metric: int


@dataclass
class IPv4Forwarder:
    """Longest-prefix-match IPv4 forwarding behavior."""

    routes: list[L3Route] = field(default_factory=list)

    def install_route(self, route: L3Route) -> None:
        """Install a route candidate in forwarding view."""
        existing = [
            idx
            for idx, candidate in enumerate(self.routes)
            if (
                candidate.prefix == route.prefix
                and candidate.route_type == route.route_type
                and candidate.next_hop == route.next_hop
                and candidate.outgoing_interface == route.outgoing_interface
            )
        ]
        for idx in reversed(existing):
            self.routes.pop(idx)
        self.routes.append(route)

    def remove_route(self, prefix: str, route_type: L3RouteType) -> None:
        """Remove route candidates for prefix/source type."""
        self.routes = [
            route
            for route in self.routes
            if not (route.prefix == prefix and route.route_type == route_type)
        ]

    def lookup(self, dst_ip: str) -> L3Route | None:
        """Perform best-route selection with LPM + tie-breakers."""
        dst = ip_address(dst_ip)
        candidates: list[L3Route] = [
            route
            for route in self.routes
            if dst in ip_network(route.prefix, strict=False)
        ]
        if not candidates:
            return None

        ordered = sorted(
            candidates,
            key=lambda route: (
                -self.prefix_length(route.prefix),
                route.admin_distance,
                route.metric,
                "" if route.next_hop is None else route.next_hop,
                "" if route.outgoing_interface is None else route.outgoing_interface,
                route.route_type,
            ),
        )
        return ordered[0]

    def forward(self, packet: PacketStack) -> tuple[str | None, PacketStack | None, str | None]:
        """Return (egress_if, forwarded_packet, drop_reason)."""
        ip_idx = next(
            (idx for idx, header in enumerate(packet.headers) if isinstance(header, IPv4Header)),
            None,
        )
        if ip_idx is None:
            return None, None, "no_ipv4_header"

        ip_header = packet.headers[ip_idx]
        if ip_header.ttl <= 1:
            return None, None, "ttl_expired"

        route = self.lookup(ip_header.dst_ip)
        if route is None:
            return None, None, "no_route"
        if route.outgoing_interface is None:
            return None, None, "no_egress_interface"

        forwarded = packet.clone()
        forwarded.headers[ip_idx] = replace(ip_header, ttl=ip_header.ttl - 1)
        return route.outgoing_interface, forwarded, None

    @staticmethod
    def prefix_length(prefix: str) -> int:
        """Helper to expose parsed prefix length."""
        return ip_network(prefix, strict=False).prefixlen
