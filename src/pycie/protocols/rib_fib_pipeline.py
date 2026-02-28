"""Lab 39: route-programming pipeline from RIB to FIB/LFIB."""

from __future__ import annotations

from dataclasses import dataclass, field
from ipaddress import ip_address, ip_network

from pycie.telemetry.events import EventType, Layer
from pycie.telemetry.trace import emit_from_env


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
    trace_node: str = "rib-fib"

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
        candidates = self._ordered_candidates_for_prefix(prefix)
        if not candidates:
            return None
        return candidates[0]

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
            candidates = self._ordered_candidates_for_prefix(prefix)
            self._emit_trace(
                event_type=EventType.RIB_CANDIDATE_EVALUATE,
                details={
                    "prefix": prefix,
                    "candidate_count": len(candidates),
                },
            )
            trace: list[PipelineStep] = [
                PipelineStep(prefix, "candidate_count", str(len(candidates)))
            ]
            if not candidates:
                trace.append(PipelineStep(prefix, "skip", "no_candidate"))
                self._emit_trace(
                    event_type=EventType.RIB_ROUTE_SKIP,
                    details={
                        "prefix": prefix,
                        "reason": "no_candidate",
                    },
                )
                self.traces[prefix] = trace
                continue

            installed = False
            for idx, candidate in enumerate(candidates, start=1):
                trace.append(
                    PipelineStep(
                        prefix,
                        "candidate",
                        (
                            f"{candidate.protocol} ad={candidate.admin_distance} "
                            f"metric={candidate.metric} nh={candidate.next_hop}"
                        ),
                    )
                )
                self._emit_trace(
                    event_type=EventType.RIB_CANDIDATE_EVALUATE,
                    details={
                        "prefix": prefix,
                        "candidate_rank": idx,
                        "protocol": candidate.protocol,
                        "admin_distance": candidate.admin_distance,
                        "metric": candidate.metric,
                        "next_hop": candidate.next_hop,
                    },
                )
                resolved = self.resolve_next_hop(candidate.next_hop)
                if resolved is None:
                    trace.append(
                        PipelineStep(
                            prefix,
                            "candidate_unresolved",
                            f"nh={candidate.next_hop}",
                        )
                    )
                    self._emit_trace(
                        event_type=EventType.RIB_ROUTE_SKIP,
                        details={
                            "prefix": prefix,
                            "reason": "candidate_unresolved",
                            "protocol": candidate.protocol,
                            "next_hop": candidate.next_hop,
                        },
                    )
                    continue

                egress_if, resolved_next_hop = resolved
                self.fib[prefix] = FIBEntry(
                    prefix=prefix,
                    egress_if=egress_if,
                    next_hop=resolved_next_hop,
                    source_protocol=candidate.protocol,
                )
                trace.append(
                    PipelineStep(
                        prefix,
                        "selected",
                        (
                            f"{candidate.protocol} ad={candidate.admin_distance} "
                            f"metric={candidate.metric} nh={candidate.next_hop}"
                        ),
                    )
                )
                trace.append(
                    PipelineStep(
                        prefix,
                        "installed",
                        f"egress={egress_if} nh={resolved_next_hop}",
                    )
                )
                self._emit_trace(
                    event_type=EventType.RIB_ROUTE_INSTALL,
                    details={
                        "prefix": prefix,
                        "egress_if": egress_if,
                        "resolved_next_hop": resolved_next_hop,
                        "source_protocol": candidate.protocol,
                        "candidate_next_hop": candidate.next_hop,
                    },
                )
                installed = True
                break

            if not installed:
                trace.append(PipelineStep(prefix, "skip", "unresolved_next_hop"))
                self._emit_trace(
                    event_type=EventType.RIB_ROUTE_SKIP,
                    details={
                        "prefix": prefix,
                        "reason": "unresolved_next_hop",
                    },
                )
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

    def _ordered_candidates_for_prefix(self, prefix: str) -> list[PipelineRoute]:
        return sorted(
            (route for route in self.routes if route.prefix == prefix),
            key=lambda route: (
                route.admin_distance,
                route.metric,
                route.protocol,
                route.next_hop,
            ),
        )

    def _emit_trace(self, *, event_type: EventType, details: dict[str, object]) -> None:
        emit_from_env(
            sim_time_ms=0,
            node=self.trace_node,
            layer=Layer.L3,
            event_type=event_type,
            details=details,
        )
