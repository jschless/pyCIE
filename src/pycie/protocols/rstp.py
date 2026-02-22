"""Lab 10: simplified RSTP scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field

from pycie.sim.network import Frame

from .base import ProtocolBase


@dataclass(frozen=True, order=True)
class RSTPBridgeId:
    priority: int
    mac: str


@dataclass(frozen=True)
class RSTPBPDU:
    root_id: RSTPBridgeId
    cost: int
    bridge_id: RSTPBridgeId
    port_id: int
    proposal: bool = False
    agreement: bool = False


@dataclass
class RSTPPort:
    if_name: str
    port_id: int
    role: str = "DESIGNATED"
    state: str = "DISCARDING"
    proposed: bool = False
    agreed: bool = False


@dataclass
class RSTPProcess(ProtocolBase):
    """Simplified rapid spanning-tree process.

    Reading:
    - IEEE 802.1w concepts (proposal/agreement)
    """

    name: str = "rstp"
    bridge_priority: int = 32768
    bridge_mac: str = "00:00:00:00:00:00"
    ports: dict[str, RSTPPort] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.bridge_id = RSTPBridgeId(self.bridge_priority, self.bridge_mac)
        self.root_id = self.bridge_id
        self.root_port: str | None = None

    def on_start(self) -> None:
        """Bootstrap RSTP and transmit initial BPDUs."""
        self.root_id = self.bridge_id
        self.root_port = None
        for port in self.ports.values():
            port.role = "DESIGNATED"
            port.state = "FORWARDING"
            port.proposed = False
            port.agreed = False

    def on_frame(self, ingress_if: str, frame: Frame) -> None:
        """Handle inbound RSTP BPDU payloads."""
        if isinstance(frame.payload, RSTPBPDU):
            self.process_bpdu(ingress_if, frame.payload)

    def process_bpdu(self, ingress_if: str, bpdu: RSTPBPDU) -> None:
        """Apply proposal/agreement and role-selection behavior."""
        port = self.ports.get(ingress_if)
        if port is None:
            return

        if bpdu.root_id < self.root_id:
            self.root_id = bpdu.root_id
            self.root_port = ingress_if

        if self.root_port == ingress_if:
            port.role = "ROOT"
            port.state = "FORWARDING"
        else:
            port.role = "DESIGNATED"

        port.proposed = bpdu.proposal
        if bpdu.proposal:
            port.agreed = True
            port.state = "FORWARDING"
        elif not bpdu.agreement:
            port.state = "DISCARDING"
        else:
            port.agreed = True
            port.state = "FORWARDING"

    def transmit_bpdu(self, if_name: str, proposal: bool, agreement: bool) -> RSTPBPDU:
        """Build a BPDU reflecting current root/port state."""
        port = self.ports[if_name]
        return RSTPBPDU(
            root_id=self.root_id,
            cost=0 if self.root_id == self.bridge_id else 4,
            bridge_id=self.bridge_id,
            port_id=port.port_id,
            proposal=proposal,
            agreement=agreement,
        )
