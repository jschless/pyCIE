"""Lab 02: simplified spanning tree protocol scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field

from pycie.sim.network import Frame

from .base import ProtocolBase


@dataclass(frozen=True, order=True)
class BridgeId:
    priority: int
    mac: str


@dataclass(frozen=True)
class BPDU:
    root_id: BridgeId
    root_path_cost: int
    bridge_id: BridgeId
    port_id: int
    hello_time_ms: int = 2_000
    max_age_ms: int = 20_000


@dataclass
class STPPort:
    if_name: str
    port_id: int
    path_cost: int = 4
    role: str = "DESIGNATED"
    state: str = "FORWARDING"


@dataclass
class STPProcess(ProtocolBase):
    """Simplified 802.1D-style spanning tree process.

    Reading:
    - IEEE 802.1D bridge protocol and BPDU ordering
    """

    name: str = "stp"
    bridge_priority: int = 32768
    bridge_mac: str = "00:00:00:00:00:00"
    ports: dict[str, STPPort] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.bridge_id = BridgeId(self.bridge_priority, self.bridge_mac)
        self.root_id = self.bridge_id
        self.root_cost = 0
        self.root_port: str | None = None

    def on_start(self) -> None:
        """Initialize local state and transmit initial BPDUs."""
        self.root_id = self.bridge_id
        self.root_cost = 0
        self.root_port = None
        self.recompute_port_states()

    def on_frame(self, ingress_if: str, frame: Frame) -> None:
        """Process incoming BPDU frames only."""
        if isinstance(frame.payload, BPDU):
            self.process_bpdu(ingress_if, frame.payload)

    def build_bpdu(self, egress_if: str) -> BPDU:
        """Build the BPDU announced on a given port."""
        port = self.ports[egress_if]
        return BPDU(
            root_id=self.root_id,
            root_path_cost=self.root_cost,
            bridge_id=self.bridge_id,
            port_id=port.port_id,
        )

    def process_bpdu(self, ingress_if: str, bpdu: BPDU) -> None:
        """Update root selection and port roles from an inbound BPDU."""
        if ingress_if not in self.ports:
            return

        ingress_port = self.ports[ingress_if]
        candidate = (
            bpdu.root_id,
            bpdu.root_path_cost + ingress_port.path_cost,
            bpdu.bridge_id,
            bpdu.port_id,
        )

        if self.root_port is None:
            local_port_id = 0
        else:
            local_port_id = self.ports[self.root_port].port_id

        local = (
            self.root_id,
            self.root_cost,
            self.bridge_id,
            local_port_id,
        )

        if candidate < local:
            self.root_id = bpdu.root_id
            self.root_cost = bpdu.root_path_cost + ingress_port.path_cost
            self.root_port = ingress_if
            self.recompute_port_states()

    def recompute_port_states(self) -> None:
        """Set each port role/state after root calculation."""
        if self.root_id == self.bridge_id or self.root_port is None:
            self.root_port = None
            for port in self.ports.values():
                port.role = "DESIGNATED"
                port.state = "FORWARDING"
            return

        for if_name, port in self.ports.items():
            if if_name == self.root_port:
                port.role = "ROOT"
                port.state = "FORWARDING"
            else:
                port.role = "ALTERNATE"
                port.state = "BLOCKING"

    def should_forward_data(self, if_name: str) -> bool:
        """Return True if the port is in a forwarding state."""
        port = self.ports.get(if_name)
        if port is None:
            return False
        return port.state == "FORWARDING"
