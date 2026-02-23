"""IPv4 forwarding pipeline scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import StrEnum
from ipaddress import ip_address, ip_network

from pycie.model.headers import IPv4Header
from pycie.model.packet import PacketStack
from pycie.telemetry.events import EventType, Layer
from pycie.telemetry.packet import ensure_packet_id
from pycie.telemetry.trace import emit_from_env


class L3RouteType(StrEnum):
    CONNECTED = "connected"
    STATIC = "static"
    OSPF = "ospf"
    BGP = "bgp"
    LDP = "ldp"


@dataclass(frozen=True)
class L3Route:
    prefix: str
    next_hop: str | None
    outgoing_interface: str | None
    route_type: "L3RouteType | str"
    admin_distance: int
    metric: int


@dataclass
class IPv4Forwarder:
    """Longest-prefix-match IPv4 forwarding behavior."""

    routes: list[L3Route] = field(default_factory=list)
    trace_node: str = "l3-forwarder"

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

    def remove_route(self, prefix: str, route_type: "L3RouteType | str") -> None:
        """Remove route candidates for prefix/source type."""
        normalized_route_type = L3RouteType(route_type)
        self.routes = [
            route
            for route in self.routes
            if not (
                route.prefix == prefix
                and L3RouteType(route.route_type) == normalized_route_type
            )
        ]

    def lookup(self, dst_ip: str) -> L3Route | None:
        """Perform best-route selection with LPM + tie-breakers."""
        dst = ip_address(dst_ip)
        candidates: list[L3Route] = [
            route
            for route in self.routes
            if dst in ip_network(route.prefix, strict=False)
        ]
        self._emit_trace(
            event_type=EventType.ROUTE_LOOKUP,
            details={
                "dst_ip": dst_ip,
                "candidate_count": len(candidates),
            },
        )
        if not candidates:
            self._emit_trace(
                event_type=EventType.ROUTE_SELECT,
                details={
                    "dst_ip": dst_ip,
                    "selected_prefix": None,
                    "next_hop": None,
                    "ad": None,
                    "metric": None,
                    "reason": "no_route",
                },
            )
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
        selected = ordered[0]
        self._emit_trace(
            event_type=EventType.ROUTE_SELECT,
            details={
                "dst_ip": dst_ip,
                "selected_prefix": selected.prefix,
                "next_hop": selected.next_hop,
                "ad": selected.admin_distance,
                "metric": selected.metric,
                "reason": "lpm_ad_metric_next_hop_interface_type",
            },
        )
        return selected

    def forward(self, packet: PacketStack) -> tuple[str | None, PacketStack | None, str | None]:
        """Return (egress_if, forwarded_packet, drop_reason)."""
        packet_id = ensure_packet_id(packet)
        ip_idx = next(
            (idx for idx, header in enumerate(packet.headers) if isinstance(header, IPv4Header)),
            None,
        )
        if ip_idx is None:
            self._emit_trace(
                event_type=EventType.FIB_DROP,
                packet_id=packet_id,
                details={"drop_reason": "no_ipv4_header"},
            )
            return None, None, "no_ipv4_header"

        ip_header = packet.headers[ip_idx]
        if ip_header.ttl <= 1:
            self._emit_trace(
                event_type=EventType.FIB_DROP,
                packet_id=packet_id,
                details={
                    "dst_ip": ip_header.dst_ip,
                    "drop_reason": "ttl_expired",
                },
            )
            return None, None, "ttl_expired"

        route = self.lookup(ip_header.dst_ip)
        if route is None:
            self._emit_trace(
                event_type=EventType.FIB_DROP,
                packet_id=packet_id,
                details={
                    "dst_ip": ip_header.dst_ip,
                    "drop_reason": "no_route",
                },
            )
            return None, None, "no_route"
        if route.outgoing_interface is None:
            self._emit_trace(
                event_type=EventType.FIB_DROP,
                packet_id=packet_id,
                details={
                    "dst_ip": ip_header.dst_ip,
                    "drop_reason": "no_egress_interface",
                    "selected_prefix": route.prefix,
                    "next_hop": route.next_hop,
                    "ad": route.admin_distance,
                    "metric": route.metric,
                },
            )
            return None, None, "no_egress_interface"

        forwarded = packet.clone()
        forwarded.headers[ip_idx] = replace(ip_header, ttl=ip_header.ttl - 1)
        self._emit_trace(
            event_type=EventType.FIB_FORWARD,
            packet_id=packet_id,
            details={
                "dst_ip": ip_header.dst_ip,
                "egress_if": route.outgoing_interface,
                "selected_prefix": route.prefix,
                "next_hop": route.next_hop,
                "ad": route.admin_distance,
                "metric": route.metric,
            },
        )
        return route.outgoing_interface, forwarded, None

    @staticmethod
    def prefix_length(prefix: str) -> int:
        """Helper to expose parsed prefix length."""
        return ip_network(prefix, strict=False).prefixlen

    def _emit_trace(
        self,
        *,
        event_type: EventType,
        details: dict[str, object],
        packet_id: str | None = None,
    ) -> None:
        emit_from_env(
            sim_time_ms=0,
            node=self.trace_node,
            layer=Layer.L3,
            event_type=event_type,
            packet_id=packet_id,
            details=details,
        )
