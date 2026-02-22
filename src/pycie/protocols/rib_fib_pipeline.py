"""Lab 39: route-programming pipeline from RIB to FIB/LFIB."""

from __future__ import annotations

from dataclasses import dataclass, field
from ipaddress import ip_address, ip_network


@dataclass(frozen=True)
class PipelineRoute:
    prefix: str
    next_hop: str
    protocol: str
    admin_distance: int
    metric: int


@dataclass(frozen=True)
class NextHopResolution:
    next_hop: str
    egress_if: str
    recursive_next_hop: str | None = None


@dataclass(frozen=True)
class FIBEntry:
    prefix: str
    egress_if: str
    next_hop: str
    source_protocol: str


@dataclass(frozen=True)
class PipelineStep:
    prefix: str
    step: str
    detail: str


@dataclass
class RIBFIBPipeline:
    """Deterministic best-route and next-hop programming pipeline."""

    routes: list[PipelineRoute] = field(default_factory=list)
    next_hops: dict[str, NextHopResolution] = field(default_factory=dict)
    fib: dict[str, FIBEntry] = field(default_factory=dict)
    traces: dict[str, list[PipelineStep]] = field(default_factory=dict)

    def install_route(self, route: PipelineRoute) -> None:
        self.routes = [
            candidate
            for candidate in self.routes
            if not (
                candidate.prefix == route.prefix
                and candidate.protocol == route.protocol
                and candidate.next_hop == route.next_hop
            )
        ]
        self.routes.append(route)

    def withdraw_route(self, prefix: str, protocol: str, *, next_hop: str | None = None) -> None:
        self.routes = [
            route
            for route in self.routes
            if not (
                route.prefix == prefix
                and route.protocol == protocol
                and (next_hop is None or route.next_hop == next_hop)
            )
        ]

    def set_next_hop_resolution(self, resolution: NextHopResolution) -> None:
        self.next_hops[resolution.next_hop] = resolution

    def best_route_for_prefix(self, prefix: str) -> PipelineRoute | None:
        candidates = [route for route in self.routes if route.prefix == prefix]
        if not candidates:
            return None
        ordered = sorted(
            candidates,
            key=lambda route: (
                route.admin_distance,
                route.metric,
                route.protocol,
                route.next_hop,
            ),
        )
        return ordered[0]

    def resolve_next_hop(self, next_hop: str, *, max_depth: int = 8) -> tuple[str, str] | None:
        visited: set[str] = set()
        current = next_hop
        depth = 0

        while depth < max_depth:
            if current in visited:
                return None
            visited.add(current)

            resolution = self.next_hops.get(current)
            if resolution is None:
                return None
            if resolution.recursive_next_hop is None:
                return resolution.egress_if, current
            current = resolution.recursive_next_hop
            depth += 1

        return None

    def recompute(self) -> None:
        self.fib = {}
        self.traces = {}

        prefixes = sorted(
            {route.prefix for route in self.routes},
            key=lambda prefix: (
                -ip_network(prefix, strict=False).prefixlen,
                prefix,
            ),
        )

        for prefix in prefixes:
            trace: list[PipelineStep] = [PipelineStep(prefix, "candidate_count", str(sum(1 for route in self.routes if route.prefix == prefix)))]
            best = self.best_route_for_prefix(prefix)
            if best is None:
                trace.append(PipelineStep(prefix, "skip", "no_candidate"))
                self.traces[prefix] = trace
                continue

            trace.append(
                PipelineStep(
                    prefix,
                    "selected",
                    f"{best.protocol} ad={best.admin_distance} metric={best.metric} nh={best.next_hop}",
                )
            )

            resolved = self.resolve_next_hop(best.next_hop)
            if resolved is None:
                trace.append(PipelineStep(prefix, "skip", "unresolved_next_hop"))
                self.traces[prefix] = trace
                continue

            egress_if, resolved_next_hop = resolved
            self.fib[prefix] = FIBEntry(
                prefix=prefix,
                egress_if=egress_if,
                next_hop=resolved_next_hop,
                source_protocol=best.protocol,
            )
            trace.append(PipelineStep(prefix, "installed", f"egress={egress_if} nh={resolved_next_hop}"))
            self.traces[prefix] = trace

    def lookup(self, dst_ip: str) -> FIBEntry | None:
        destination = ip_address(dst_ip)
        matches = [
            entry
            for entry in self.fib.values()
            if destination in ip_network(entry.prefix, strict=False)
        ]
        if not matches:
            return None
        return sorted(
            matches,
            key=lambda entry: (
                -ip_network(entry.prefix, strict=False).prefixlen,
                entry.prefix,
            ),
        )[0]

    def explain(self, prefix: str) -> list[PipelineStep]:
        return list(self.traces.get(prefix, []))
