"""Lab 30: route selection and redistribution decision model."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from ipaddress import ip_address, ip_network


class RouteProtocol(StrEnum):
    CONNECTED = "connected"
    STATIC = "static"
    OSPF = "ospf"
    ISIS = "isis"
    BGP = "bgp"
    REDISTRIBUTED = "redistributed"


DEFAULT_ADMIN_DISTANCE: dict[RouteProtocol, int] = {
    RouteProtocol.CONNECTED: 0,
    RouteProtocol.STATIC: 1,
    RouteProtocol.OSPF: 110,
    RouteProtocol.ISIS: 115,
    RouteProtocol.BGP: 200,
    RouteProtocol.REDISTRIBUTED: 210,
}


@dataclass(frozen=True)
class RouteCandidate:
    prefix: str
    next_hop: str
    protocol: "RouteProtocol | str"
    admin_distance: int
    metric: int
    tags: frozenset[str] = frozenset()


@dataclass(frozen=True)
class DecisionTrace:
    dst_ip: str
    candidates: tuple[RouteCandidate, ...]
    selected: RouteCandidate | None
    reason: str


@dataclass
class RouteSelectionEngine:
    """Deterministic route selection with explainable decisions."""

    routes: list[RouteCandidate] = field(default_factory=list)

    def install_route(self, route: RouteCandidate) -> None:
        """Install or replace route candidate."""
        self.routes = [
            candidate
            for candidate in self.routes
            if not (
                candidate.prefix == route.prefix
                and RouteProtocol(candidate.protocol) == RouteProtocol(route.protocol)
                and candidate.next_hop == route.next_hop
            )
        ]
        self.routes.append(route)

    def withdraw_route(
        self,
        prefix: str,
        protocol: "RouteProtocol | str",
        *,
        next_hop: str | None = None,
    ) -> None:
        """Withdraw matching route candidates."""
        normalized_protocol = RouteProtocol(protocol)
        self.routes = [
            route
            for route in self.routes
            if not (
                route.prefix == prefix
                and RouteProtocol(route.protocol) == normalized_protocol
                and (next_hop is None or route.next_hop == next_hop)
            )
        ]

    def best_route(self, dst_ip: str) -> RouteCandidate | None:
        """Select best route using LPM -> AD -> metric -> deterministic tie-breakers."""
        matches = self._matching_candidates(dst_ip)
        if not matches:
            return None
        return sorted(matches, key=self._candidate_rank_key)[0]

    def explain(self, dst_ip: str) -> DecisionTrace:
        """Provide ranked candidates and reason string for a lookup."""
        matches = tuple(sorted(self._matching_candidates(dst_ip), key=self._candidate_rank_key))
        selected = matches[0] if matches else None
        reason = "no_route" if selected is None else "lpm_ad_metric_protocol_next_hop"
        return DecisionTrace(dst_ip=dst_ip, candidates=matches, selected=selected, reason=reason)

    def redistribute(
        self,
        from_protocol: "RouteProtocol | str",
        to_protocol: "RouteProtocol | str",
        *,
        route_tag: str,
        metric_increment: int = 10,
    ) -> list[RouteCandidate]:
        """Create redistributed candidates with loop-prevention tag checks."""
        src = RouteProtocol(from_protocol)
        dst = RouteProtocol(to_protocol)

        redistributed: list[RouteCandidate] = []
        for route in sorted(self.routes, key=lambda r: (r.prefix, r.next_hop, str(r.protocol))):
            if RouteProtocol(route.protocol) != src:
                continue
            if route_tag in route.tags:
                continue
            if src == dst:
                continue

            redistributed.append(
                RouteCandidate(
                    prefix=route.prefix,
                    next_hop=route.next_hop,
                    protocol=dst,
                    admin_distance=DEFAULT_ADMIN_DISTANCE.get(dst, route.admin_distance),
                    metric=route.metric + metric_increment,
                    tags=route.tags | {route_tag},
                )
            )
        return redistributed

    def _matching_candidates(self, dst_ip: str) -> list[RouteCandidate]:
        dst = ip_address(dst_ip)
        return [
            route
            for route in self.routes
            if dst in ip_network(route.prefix, strict=False)
        ]

    @staticmethod
    def _candidate_rank_key(route: RouteCandidate) -> tuple[int, int, int, str, str]:
        return (
            -ip_network(route.prefix, strict=False).prefixlen,
            route.admin_distance,
            route.metric,
            str(RouteProtocol(route.protocol)),
            route.next_hop,
        )
