"""Device model used by protocol processes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from pycie.sim.network import Frame, Interface, NetworkSimulator
from pycie.telemetry.events import EventType, Layer
from pycie.telemetry.packet import ensure_packet_id
from pycie.telemetry.pdu import frame_trace_details

if False:  # pragma: no cover
    from pycie.protocols.base import ProtocolBase


@dataclass
class Device:
    """A simulated network device hosting one or more protocol processes."""

    node_id: str
    simulator: NetworkSimulator
    interfaces: dict[str, Interface] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.protocols: dict[str, "ProtocolBase"] = {}
        self.simulator.register_receiver(self.node_id, self._receive_from_sim)

    def add_interface(self, interface: Interface) -> None:
        if interface.node_id != self.node_id:
            raise ValueError("interface node_id must match device node_id")
        self.interfaces[interface.name] = interface

    def register_protocol(self, name: str, protocol: "ProtocolBase") -> None:
        self.protocols[name] = protocol
        protocol.attach(self)

    def start(self) -> None:
        for protocol in self.protocols.values():
            protocol.on_start()

    def schedule_timer(
        self,
        delay_ms: float,
        callback: Callable[..., None],
        *args: object,
        priority: int = 100,
        **kwargs: object,
    ) -> None:
        self.simulator.schedule_in(delay_ms, callback, *args, priority=priority, **kwargs)

    def send_frame(self, egress_if: str, frame: Frame) -> None:
        packet_id = ensure_packet_id(frame)
        self.emit_trace(
            layer=Layer.L2,
            event_type=EventType.FRAME_TX,
            egress_if=egress_if,
            packet_id=packet_id,
            details=frame_trace_details(frame),
        )
        self.simulator.send_frame(self.node_id, egress_if, frame)

    def _receive_from_sim(self, node_id: str, ingress_if: str, frame: Frame) -> None:
        if node_id != self.node_id:
            return
        packet_id = ensure_packet_id(frame)
        self.emit_trace(
            layer=Layer.L2,
            event_type=EventType.FRAME_RX,
            ingress_if=ingress_if,
            packet_id=packet_id,
            details=frame_trace_details(frame),
        )
        for protocol in self.protocols.values():
            protocol.on_frame(ingress_if, frame)

    def emit_trace(
        self,
        *,
        layer: Layer | str,
        event_type: EventType | str,
        ingress_if: str | None = None,
        egress_if: str | None = None,
        packet_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Emit node-scoped trace event through simulator recorder."""
        self.simulator.emit_trace(
            node=self.node_id,
            layer=layer,
            event_type=event_type,
            ingress_if=ingress_if,
            egress_if=egress_if,
            packet_id=packet_id,
            details=details or {},
        )
