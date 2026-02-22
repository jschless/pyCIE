"""Lab 36: EVPN control-plane model."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class EVPNRouteType(StrEnum):
    RT2_MAC_IP = "rt2"
    RT5_IP_PREFIX = "rt5"


@dataclass(frozen=True)
class EVPNRoute:
    route_type: "EVPNRouteType | str"
    vni: int
    route_target: str
    next_hop: str
    mac: str | None = None
    ip: str | None = None
    prefix: str | None = None
    sequence: int = 0
    originator: str = ""


@dataclass
class EVPNControlPlane:
    """Simplified EVPN route import and best-path selection."""

    import_rts: set[str] = field(default_factory=set)
    adj_rib_in: dict[str, list[EVPNRoute]] = field(default_factory=dict)
    mac_rib: dict[tuple[int, str], EVPNRoute] = field(default_factory=dict)
    ip_rib: dict[str, EVPNRoute] = field(default_factory=dict)

    def import_route(self, peer_id: str, route: EVPNRoute) -> bool:
        """Import route if route-target matches local import policy."""
        if route.route_target not in self.import_rts:
            return False

        bucket = self.adj_rib_in.setdefault(peer_id, [])
        bucket = [candidate for candidate in bucket if self._route_key(candidate) != self._route_key(route)]
        bucket.append(route)
        self.adj_rib_in[peer_id] = bucket
        self.recompute()
        return True

    def withdraw_route(self, peer_id: str, route: EVPNRoute) -> None:
        """Withdraw peer route and recompute derived RIBs."""
        bucket = self.adj_rib_in.get(peer_id)
        if bucket is None:
            return
        self.adj_rib_in[peer_id] = [candidate for candidate in bucket if self._route_key(candidate) != self._route_key(route)]
        self.recompute()

    def recompute(self) -> None:
        """Rebuild MAC and IP route tables from Adj-RIB-In."""
        mac_candidates: dict[tuple[int, str], list[EVPNRoute]] = {}
        ip_candidates: dict[str, list[EVPNRoute]] = {}

        for bucket in self.adj_rib_in.values():
            for route in bucket:
                route_type = EVPNRouteType(route.route_type)
                if route_type == EVPNRouteType.RT2_MAC_IP and route.mac is not None:
                    mac_candidates.setdefault((route.vni, route.mac.lower()), []).append(route)
                if route_type == EVPNRouteType.RT5_IP_PREFIX and route.prefix is not None:
                    ip_candidates.setdefault(route.prefix, []).append(route)

        self.mac_rib = {
            key: sorted(
                candidates,
                key=lambda route: (
                    -route.sequence,
                    route.next_hop,
                    route.originator,
                ),
            )[0]
            for key, candidates in mac_candidates.items()
        }

        self.ip_rib = {
            prefix: sorted(
                candidates,
                key=lambda route: (
                    route.next_hop,
                    route.originator,
                ),
            )[0]
            for prefix, candidates in ip_candidates.items()
        }

    def resolve_mac(self, vni: int, mac: str) -> str | None:
        route = self.mac_rib.get((vni, mac.lower()))
        return None if route is None else route.next_hop

    def resolve_prefix(self, prefix: str) -> str | None:
        route = self.ip_rib.get(prefix)
        return None if route is None else route.next_hop

    @staticmethod
    def _route_key(route: EVPNRoute) -> tuple[str, int, str | None, str | None]:
        route_type = EVPNRouteType(route.route_type)
        if route_type == EVPNRouteType.RT2_MAC_IP:
            return (route_type, route.vni, route.mac.lower() if route.mac else None, route.ip)
        return (route_type, route.vni, route.prefix, None)
