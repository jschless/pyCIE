"""Lab 06c: IP addressing, prefix matching, and MAC adjacency basics."""

from __future__ import annotations

from dataclasses import dataclass, field
from ipaddress import ip_address, ip_network

from .base import ProtocolBase


@dataclass(frozen=True)
class InterfaceAddress:
    if_name: str
    prefix: str
    mac: str


@dataclass(frozen=True)
class StaticRoute:
    prefix: str
    next_hop: str
    outgoing_interface: str
    admin_distance: int = 1
    metric: int = 0


@dataclass(frozen=True)
class LookupExplanation:
    destination: str
    selected_prefix: str
    prefix_length: int
    outgoing_interface: str
    next_hop_ip: str
    connected: bool
    admin_distance: int
    metric: int
    reason: str


@dataclass
class IPMacBasicsProcess(ProtocolBase):
    """Explainable IPv4 route lookup and adjacency resolution."""

    name: str = "ip_mac_basics"
    interfaces: dict[str, InterfaceAddress] = field(default_factory=dict)
    static_routes: list[StaticRoute] = field(default_factory=list)
    arp_table: dict[str, str] = field(default_factory=dict)

    def add_interface(self, *, if_name: str, prefix: str, mac: str) -> None:
        self.interfaces[if_name] = InterfaceAddress(if_name=if_name, prefix=prefix, mac=mac)

    def add_static_route(
        self,
        *,
        prefix: str,
        next_hop: str,
        outgoing_interface: str,
        admin_distance: int = 1,
        metric: int = 0,
    ) -> None:
        self.static_routes = [
            route
            for route in self.static_routes
            if not (
                route.prefix == prefix
                and route.next_hop == next_hop
                and route.outgoing_interface == outgoing_interface
            )
        ]
        self.static_routes.append(
            StaticRoute(
                prefix=prefix,
                next_hop=next_hop,
                outgoing_interface=outgoing_interface,
                admin_distance=admin_distance,
                metric=metric,
            )
        )

    def learn_arp(self, *, ip: str, mac: str) -> None:
        self.arp_table[ip] = mac

    def explain_lookup(self, destination: str) -> LookupExplanation | None:
        dst = ip_address(destination)
        candidates: list[LookupExplanation] = []

        for interface in self.interfaces.values():
            network = ip_network(interface.prefix, strict=False)
            if dst in network:
                candidates.append(
                    LookupExplanation(
                        destination=destination,
                        selected_prefix=str(network),
                        prefix_length=network.prefixlen,
                        outgoing_interface=interface.if_name,
                        next_hop_ip=destination,
                        connected=True,
                        admin_distance=0,
                        metric=0,
                        reason="connected_lpm",
                    )
                )

        for route in self.static_routes:
            network = ip_network(route.prefix, strict=False)
            if dst not in network:
                continue
            candidates.append(
                LookupExplanation(
                    destination=destination,
                    selected_prefix=str(network),
                    prefix_length=network.prefixlen,
                    outgoing_interface=route.outgoing_interface,
                    next_hop_ip=route.next_hop,
                    connected=False,
                    admin_distance=route.admin_distance,
                    metric=route.metric,
                    reason="static_lpm_ad_metric",
                )
            )

        if not candidates:
            return None

        return sorted(
            candidates,
            key=lambda value: (
                -value.prefix_length,
                value.admin_distance,
                value.metric,
                value.connected is False,
                value.outgoing_interface,
                value.next_hop_ip,
            ),
        )[0]

    def forward_decision(self, destination: str) -> tuple[str | None, str | None, str | None]:
        """Return egress interface, resolved destination MAC, and optional drop reason."""
        explanation = self.explain_lookup(destination)
        if explanation is None:
            return None, None, "no_route"

        resolved_mac = self.arp_table.get(explanation.next_hop_ip)
        if resolved_mac is None:
            return explanation.outgoing_interface, None, "mac_unresolved"

        return explanation.outgoing_interface, resolved_mac, None

    def prefix_details(self, prefix: str) -> dict[str, str | int]:
        network = ip_network(prefix, strict=False)
        return {
            "network": str(network.network_address),
            "netmask": str(network.netmask),
            "hostmask": str(network.hostmask),
            "prefix_length": network.prefixlen,
        }
