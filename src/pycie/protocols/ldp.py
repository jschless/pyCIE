"""Lab 05: simplified LDP protocol scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from pycie.sim.network import Frame

from .base import ProtocolBase


@dataclass(frozen=True)
class LDPHello:
    router_id: str


@dataclass(frozen=True)
class LabelMapping:
    prefix: str
    label: int
    next_hop: str


class LDPNeighborState(StrEnum):
    DOWN = "DOWN"
    UP = "UP"


@dataclass
class LDPNeighbor:
    router_id: str
    state: "LDPNeighborState | str" = LDPNeighborState.DOWN


@dataclass
class LDPProcess(ProtocolBase):
    """Simplified downstream-unsolicited LDP process.

    Reading:
    - RFC 5036
    - RFC 3031 (MPLS architecture)
    """

    name: str = "ldp"
    router_id: str = "0.0.0.0"
    neighbors: dict[str, LDPNeighbor] = field(default_factory=dict)
    lib: dict[str, int] = field(default_factory=dict)
    remote_bindings: dict[str, dict[str, int]] = field(default_factory=dict)
    label_counter: int = 16

    def on_start(self) -> None:
        """Send discovery hellos and advertise initial local bindings."""
        # Discovery signaling is out of scope for the scaffold baseline.

    def on_frame(self, ingress_if: str, frame: Frame) -> None:
        """Handle hello and label mapping messages."""
        payload = frame.payload
        if isinstance(payload, LDPHello):
            self.neighbors[payload.router_id] = LDPNeighbor(
                router_id=payload.router_id,
                state=LDPNeighborState.UP,
            )
        if isinstance(payload, LabelMapping):
            self.process_label_mapping(ingress_if, payload)

    def allocate_local_label(self, prefix: str) -> int:
        """Allocate (or return existing) local label for prefix."""
        if prefix in self.lib:
            return self.lib[prefix]
        label = self.label_counter
        self.label_counter += 1
        self.lib[prefix] = label
        return label

    def advertise_bindings(self) -> list[LabelMapping]:
        """Build current outbound label mapping set."""
        return [
            LabelMapping(prefix=prefix, label=label, next_hop=self.router_id)
            for prefix, label in sorted(self.lib.items())
        ]

    def process_label_mapping(self, peer_id: str, mapping: LabelMapping) -> None:
        """Store peer binding and trigger LFIB update."""
        self.remote_bindings.setdefault(peer_id, {})[mapping.prefix] = mapping.label

    def build_lfib(self) -> dict[str, tuple[int, int | None]]:
        """Return prefix -> (out_label, in_label_or_none) mapping."""
        lfib: dict[str, tuple[int, int | None]] = {}
        for prefix, local_label in sorted(self.lib.items()):
            out_label = local_label
            for neighbor in sorted(self.remote_bindings):
                remote = self.remote_bindings[neighbor]
                if prefix in remote:
                    out_label = remote[prefix]
                    break
            lfib[prefix] = (out_label, local_label)
        return lfib
