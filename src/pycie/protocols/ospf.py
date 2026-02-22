"""Lab 03: simplified OSPF protocol scaffold."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from enum import StrEnum

from pycie.sim.network import Frame

from .base import ProtocolBase


@dataclass(frozen=True)
class OSPFHello:
    router_id: str
    area_id: int
    hello_interval_ms: int
    dead_interval_ms: int
    neighbors: tuple[str, ...]


@dataclass(frozen=True)
class RouterLSA:
    advertising_router: str
    lsa_id: str
    sequence: int
    links: tuple[tuple[str, int], ...]


class OSPFNeighborState(StrEnum):
    DOWN = "DOWN"
    INIT = "INIT"
    TWO_WAY = "2WAY"
    FULL = "FULL"


@dataclass
class OSPFNeighbor:
    router_id: str
    state: "OSPFNeighborState | str" = OSPFNeighborState.DOWN
    dead_interval_ms: int = 40_000
    last_hello_ms: float = 0.0


@dataclass
class OSPFProcess(ProtocolBase):
    """Simplified single-area OSPF process.

    Reading:
    - RFC 2328 sections 7-13
    """

    name: str = "ospf"
    router_id: str = "0.0.0.0"
    area_id: int = 0
    hello_interval_ms: int = 10_000
    dead_interval_ms: int = 40_000
    neighbors: dict[str, OSPFNeighbor] = field(default_factory=dict)
    lsdb: dict[str, RouterLSA] = field(default_factory=dict)

    def on_start(self) -> None:
        """Start hello timers and originate initial LSA."""
        lsa = self.originate_router_lsa()
        self.install_lsa(lsa)

    def on_frame(self, ingress_if: str, frame: Frame) -> None:
        """Dispatch inbound hello and LSA payloads."""
        if isinstance(frame.payload, OSPFHello):
            self.process_hello(ingress_if, frame.payload)
        if isinstance(frame.payload, RouterLSA):
            self.install_lsa(frame.payload)

    def send_hello(self) -> None:
        """Send hello packets on all enabled interfaces."""
        # Intentionally no-op for the scaffold baseline.

    def process_hello(self, ingress_if: str, hello: OSPFHello) -> None:
        """Update neighbor state machine on hello reception."""
        if hello.area_id != self.area_id:
            return

        neighbor = self.neighbors.get(hello.router_id)
        if neighbor is None:
            neighbor = OSPFNeighbor(router_id=hello.router_id)
            self.neighbors[hello.router_id] = neighbor

        if self.router_id in hello.neighbors:
            neighbor.state = OSPFNeighborState.FULL
        else:
            neighbor.state = OSPFNeighborState.INIT

        neighbor.dead_interval_ms = hello.dead_interval_ms
        neighbor.last_hello_ms = self.now_ms if hasattr(self, "device") else 0.0

    def originate_router_lsa(self) -> RouterLSA:
        """Create a self-originated router LSA from local links."""
        current = self.lsdb.get(self.router_id)
        seq = current.sequence + 1 if current else 1

        links: list[tuple[str, int]] = []
        if hasattr(self, "device"):
            for if_name, interface in sorted(self.device.interfaces.items()):
                # Use a stable pseudo-node identifier for local interfaces in the baseline.
                links.append((f"{self.router_id}:{if_name}", interface.cost))

        return RouterLSA(
            advertising_router=self.router_id,
            lsa_id=self.router_id,
            sequence=seq,
            links=tuple(links),
        )

    def install_lsa(self, lsa: RouterLSA) -> bool:
        """Install a newer LSA and return whether LSDB changed."""
        current = self.lsdb.get(lsa.advertising_router)
        if current is None or lsa.sequence > current.sequence:
            self.lsdb[lsa.advertising_router] = lsa
            return True
        return False

    def run_spf(self) -> dict[str, tuple[int, str | None]]:
        """Compute shortest paths and return next-hop view per router ID."""
        if self.router_id not in self.lsdb:
            return {self.router_id: (0, None)}

        distances: dict[str, int] = {self.router_id: 0}
        first_hop: dict[str, str | None] = {self.router_id: None}
        queue: list[tuple[int, str]] = [(0, self.router_id)]

        while queue:
            cost, node = heapq.heappop(queue)
            if cost > distances.get(node, 10**9):
                continue

            lsa = self.lsdb.get(node)
            if lsa is None:
                continue

            for neighbor, edge_cost in lsa.links:
                new_cost = cost + edge_cost
                known = distances.get(neighbor)
                candidate_first_hop = neighbor if node == self.router_id else first_hop[node]

                if known is None or new_cost < known:
                    distances[neighbor] = new_cost
                    first_hop[neighbor] = candidate_first_hop
                    heapq.heappush(queue, (new_cost, neighbor))
                elif new_cost == known:
                    current_hop = first_hop.get(neighbor)
                    if current_hop is None or (
                        candidate_first_hop is not None and candidate_first_hop < current_hop
                    ):
                        first_hop[neighbor] = candidate_first_hop

        return {
            node: (distances[node], first_hop.get(node))
            for node in sorted(distances)
        }

    def compute_routing_table(self) -> dict[str, str | None]:
        """Build destination -> next-hop map from SPF output."""
        spf = self.run_spf()
        return {
            destination: next_hop
            for destination, (_cost, next_hop) in spf.items()
            if destination != self.router_id
        }
