"""Lab 23: simplified IS-IS L1/L2 scaffold."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field

from pycie.sim.network import Frame

from .base import ProtocolBase


@dataclass(frozen=True)
class ISISLSP:
    system_id: str
    level: int
    sequence: int
    links: tuple[tuple[str, int], ...]
    overload: bool = False


@dataclass(frozen=True)
class ISISNeighbor:
    system_id: str
    metric: int = 10
    levels: tuple[int, ...] = (1, 2)


@dataclass
class ISISProcess(ProtocolBase):
    """Simplified IS-IS process with per-level LSDB and SPF."""

    name: str = "isis"
    system_id: str = "0000.0000.0000"
    level1_enabled: bool = True
    level2_enabled: bool = True
    neighbors: dict[str, ISISNeighbor] = field(default_factory=dict)
    lsdb: dict[tuple[int, str], ISISLSP] = field(default_factory=dict)

    def on_start(self) -> None:
        """Originate initial local LSPs for enabled levels."""
        if self.level1_enabled:
            self.install_lsp(self.originate_lsp(1))
        if self.level2_enabled:
            self.install_lsp(self.originate_lsp(2))

    def on_frame(self, ingress_if: str, frame: Frame) -> None:
        """Process inbound IS-IS LSP payloads."""
        if isinstance(frame.payload, ISISLSP):
            self.install_lsp(frame.payload)

    def set_neighbor(self, neighbor: ISISNeighbor) -> None:
        """Install or refresh a neighbor relationship."""
        self.neighbors[neighbor.system_id] = neighbor

    def originate_lsp(self, level: int) -> ISISLSP:
        """Create a self-originated LSP for a specific level."""
        current = self.lsdb.get((level, self.system_id))
        sequence = 1 if current is None else current.sequence + 1

        links = tuple(
            sorted(
                (neighbor.system_id, neighbor.metric)
                for neighbor in self.neighbors.values()
                if level in neighbor.levels
            )
        )
        return ISISLSP(
            system_id=self.system_id,
            level=level,
            sequence=sequence,
            links=links,
        )

    def install_lsp(self, lsp: ISISLSP) -> bool:
        """Install an LSP if it is newer than existing state."""
        key = (lsp.level, lsp.system_id)
        current = self.lsdb.get(key)
        if current is None or lsp.sequence > current.sequence:
            self.lsdb[key] = lsp
            return True
        return False

    def run_spf(self, level: int) -> dict[str, tuple[int, str | None]]:
        """Run Dijkstra for the selected level and return (cost, next-hop)."""
        local = self.lsdb.get((level, self.system_id))
        if local is None:
            return {self.system_id: (0, None)}

        distances: dict[str, int] = {self.system_id: 0}
        first_hop: dict[str, str | None] = {self.system_id: None}
        queue: list[tuple[int, str]] = [(0, self.system_id)]

        while queue:
            cost, node = heapq.heappop(queue)
            if cost > distances.get(node, 10**9):
                continue

            lsp = self.lsdb.get((level, node))
            if lsp is None:
                continue

            # Do not use overloaded routers as transit nodes.
            if node != self.system_id and lsp.overload:
                continue

            for neighbor, edge_cost in lsp.links:
                candidate_cost = cost + edge_cost
                known = distances.get(neighbor)
                candidate_first_hop = neighbor if node == self.system_id else first_hop[node]

                if known is None or candidate_cost < known:
                    distances[neighbor] = candidate_cost
                    first_hop[neighbor] = candidate_first_hop
                    heapq.heappush(queue, (candidate_cost, neighbor))
                elif candidate_cost == known:
                    current_hop = first_hop.get(neighbor)
                    if current_hop is None or (
                        candidate_first_hop is not None and candidate_first_hop < current_hop
                    ):
                        first_hop[neighbor] = candidate_first_hop

        return {node: (distances[node], first_hop.get(node)) for node in sorted(distances)}

    def compute_routing_table(self) -> dict[str, tuple[int, str | None, int]]:
        """Return destination -> (cost, next-hop, level)."""
        l1 = self.run_spf(1) if self.level1_enabled else {}
        l2 = self.run_spf(2) if self.level2_enabled else {}

        destinations = (set(l1) | set(l2)) - {self.system_id}
        output: dict[str, tuple[int, str | None, int]] = {}
        for destination in sorted(destinations):
            l1_route = l1.get(destination)
            l2_route = l2.get(destination)
            if l1_route is not None:
                output[destination] = (l1_route[0], l1_route[1], 1)
            elif l2_route is not None:
                output[destination] = (l2_route[0], l2_route[1], 2)
        return output
