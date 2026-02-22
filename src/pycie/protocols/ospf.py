"""Lab 03: simplified OSPF protocol scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field

from pycie.core.todo import student_todo
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


@dataclass
class OSPFNeighbor:
    router_id: str
    state: str = "DOWN"
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
        student_todo("Initialize OSPF hello and LSA flooding")

    def on_frame(self, ingress_if: str, frame: Frame) -> None:
        """Dispatch inbound hello and LSA payloads."""
        student_todo("Parse and handle OSPF control packets")

    def send_hello(self) -> None:
        """Send hello packets on all enabled interfaces."""
        student_todo("Implement periodic OSPF hello transmission")

    def process_hello(self, ingress_if: str, hello: OSPFHello) -> None:
        """Update neighbor state machine on hello reception."""
        student_todo("Implement OSPF neighbor state transitions")

    def originate_router_lsa(self) -> RouterLSA:
        """Create a self-originated router LSA from local links."""
        student_todo("Originate local router LSA")

    def install_lsa(self, lsa: RouterLSA) -> bool:
        """Install a newer LSA and return whether LSDB changed."""
        student_todo("Implement LSA sequence handling and LSDB update")

    def run_spf(self) -> dict[str, tuple[int, str | None]]:
        """Compute shortest paths and return next-hop view per router ID."""
        student_todo("Implement Dijkstra SPF over current LSDB graph")

    def compute_routing_table(self) -> dict[str, str | None]:
        """Build destination -> next-hop map from SPF output."""
        student_todo("Translate SPF tree into routing entries")
