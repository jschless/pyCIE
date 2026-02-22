"""Device model used by protocol processes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from pycie.sim.network import Frame, Interface, NetworkSimulator

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
        self.simulator.send_frame(self.node_id, egress_if, frame)

    def _receive_from_sim(self, node_id: str, ingress_if: str, frame: Frame) -> None:
        if node_id != self.node_id:
            return
        for protocol in self.protocols.values():
            protocol.on_frame(ingress_if, frame)
