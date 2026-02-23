"""Lab 02: simplified spanning tree protocol scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from pycie.sim.network import Frame
from pycie.telemetry.events import EventType, Layer
from pycie.telemetry.packet import ensure_packet_id

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


class STPRole(StrEnum):
    DESIGNATED = "DESIGNATED"
    ROOT = "ROOT"
    ALTERNATE = "ALTERNATE"


class STPState(StrEnum):
    FORWARDING = "FORWARDING"
    BLOCKING = "BLOCKING"


@dataclass
class STPPort:
    if_name: str
    port_id: int
    path_cost: int = 4
    role: "STPRole | str" = STPRole.DESIGNATED
    state: "STPState | str" = STPState.FORWARDING


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
            packet_id = ensure_packet_id(frame)
            self.emit_trace(
                layer=Layer.STP,
                event_type=EventType.STP_BPDU_RX,
                ingress_if=ingress_if,
                packet_id=packet_id,
                details={
                    "root_id": self._bridge_id_str(frame.payload.root_id),
                    "root_path_cost": frame.payload.root_path_cost,
                    "bridge_id": self._bridge_id_str(frame.payload.bridge_id),
                    "port_id": frame.payload.port_id,
                },
            )
            self.process_bpdu(ingress_if, frame.payload)

    def build_bpdu(self, egress_if: str) -> BPDU:
        """Build the BPDU announced on a given port."""
        port = self.ports[egress_if]
        bpdu = BPDU(
            root_id=self.root_id,
            root_path_cost=self.root_cost,
            bridge_id=self.bridge_id,
            port_id=port.port_id,
        )
        self.emit_trace(
            layer=Layer.STP,
            event_type=EventType.STP_BPDU_TX,
            egress_if=egress_if,
            details={
                "root_id": self._bridge_id_str(bpdu.root_id),
                "root_path_cost": bpdu.root_path_cost,
                "bridge_id": self._bridge_id_str(bpdu.bridge_id),
                "port_id": bpdu.port_id,
            },
        )
        return bpdu

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
            old_root = self.root_id
            old_cost = self.root_cost
            old_root_port = self.root_port
            self.root_id = bpdu.root_id
            self.root_cost = bpdu.root_path_cost + ingress_port.path_cost
            self.root_port = ingress_if
            self.emit_trace(
                layer=Layer.STP,
                event_type=EventType.STP_ROOT_CHANGE,
                ingress_if=ingress_if,
                details={
                    "old_root_id": self._bridge_id_str(old_root),
                    "new_root_id": self._bridge_id_str(self.root_id),
                    "old_cost": old_cost,
                    "new_cost": self.root_cost,
                    "root_port": self.root_port,
                    "previous_root_port": old_root_port,
                },
            )
            self.recompute_port_states()

    def recompute_port_states(self) -> None:
        """Set each port role/state after root calculation."""
        before = {
            if_name: (STPRole(port.role), STPState(port.state))
            for if_name, port in self.ports.items()
        }

        if self.root_id == self.bridge_id or self.root_port is None:
            self.root_port = None
            for port in self.ports.values():
                port.role = STPRole.DESIGNATED
                port.state = STPState.FORWARDING
        else:
            for if_name, port in self.ports.items():
                if if_name == self.root_port:
                    port.role = STPRole.ROOT
                    port.state = STPState.FORWARDING
                else:
                    port.role = STPRole.ALTERNATE
                    port.state = STPState.BLOCKING

        for if_name, port in self.ports.items():
            previous_role, previous_state = before.get(
                if_name,
                (STPRole.DESIGNATED, STPState.FORWARDING),
            )
            current_role = STPRole(port.role)
            current_state = STPState(port.state)
            if previous_role == current_role and previous_state == current_state:
                continue
            self.emit_trace(
                layer=Layer.STP,
                event_type=EventType.STP_PORT_ROLE_CHANGE,
                ingress_if=if_name,
                details={
                    "if_name": if_name,
                    "bridge_id": self._bridge_id_str(self.bridge_id),
                    "old_role": previous_role.value,
                    "new_role": current_role.value,
                    "old_state": previous_state.value,
                    "new_state": current_state.value,
                },
            )

    def should_forward_data(self, if_name: str) -> bool:
        """Return True if the port is in a forwarding state."""
        port = self.ports.get(if_name)
        if port is None:
            return False
        return STPState(port.state) == STPState.FORWARDING

    @staticmethod
    def _bridge_id_str(value: BridgeId) -> str:
        return f"{value.priority}:{value.mac}"
