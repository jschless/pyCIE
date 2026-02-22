"""Base protocol hooks for pyCIE labs."""

from __future__ import annotations

from dataclasses import dataclass

from pycie.sim.network import Frame

if False:  # pragma: no cover
    from pycie.core.node import Device


@dataclass
class ProtocolBase:
    """Base class for protocol processes running on a device."""

    name: str = "base"

    def attach(self, device: "Device") -> None:
        self.device = device

    @property
    def node_id(self) -> str:
        return self.device.node_id

    @property
    def now_ms(self) -> float:
        return self.device.simulator.clock.now_ms

    def on_start(self) -> None:
        """Called when the device starts protocol processes."""

    def on_frame(self, ingress_if: str, frame: Frame) -> None:
        """Called for every incoming frame."""

    def on_tick(self) -> None:
        """Optional periodic callback."""

    def on_interface_up(self, if_name: str) -> None:
        """Called when interface transitions up."""

    def on_interface_down(self, if_name: str) -> None:
        """Called when interface transitions down."""
