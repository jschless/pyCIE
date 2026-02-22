"""Lab 15: MPLS control-plane interaction scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field

from .base import ProtocolBase


@dataclass(frozen=True)
class MPLSBinding:
    fec: str
    local_label: int
    next_hop: str


@dataclass
class MPLSProcess(ProtocolBase):
    """MPLS control-plane state for FEC/label coordination."""

    name: str = "mpls"
    local_bindings: dict[str, MPLSBinding] = field(default_factory=dict)
    remote_bindings: dict[str, dict[str, int]] = field(default_factory=dict)
    label_counter: int = 16000

    def allocate_label(self, fec: str) -> int:
        """Allocate or return local label for a given FEC."""
        if fec in self.local_bindings:
            return self.local_bindings[fec].local_label

        label = self.label_counter
        self.label_counter += 1
        self.local_bindings[fec] = MPLSBinding(fec=fec, local_label=label, next_hop=self.node_id if hasattr(self, "device") else "self")
        return label

    def install_remote_binding(self, neighbor: str, fec: str, label: int) -> None:
        """Store remote label for FEC from neighbor."""
        self.remote_bindings.setdefault(neighbor, {})[fec] = label

    def build_lfib_view(self) -> dict[str, tuple[int, int | None]]:
        """Return FEC to (out_label, in_label_or_none) projection."""
        lfib: dict[str, tuple[int, int | None]] = {}
        for fec, binding in sorted(self.local_bindings.items()):
            remote_label: int | None = None
            for neighbor in sorted(self.remote_bindings):
                if fec in self.remote_bindings[neighbor]:
                    remote_label = self.remote_bindings[neighbor][fec]
                    break

            out_label = binding.local_label if remote_label is None else remote_label
            lfib[fec] = (out_label, binding.local_label)
        return lfib
