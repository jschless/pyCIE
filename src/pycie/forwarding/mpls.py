"""MPLS forwarding scaffold (push/swap/pop)."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import StrEnum

from pycie.model.headers import MPLSLabel
from pycie.model.packet import PacketStack


class MPLSOperation(StrEnum):
    PUSH = "push"
    SWAP = "swap"
    POP = "pop"


@dataclass(frozen=True)
class LFIBEntry:
    in_label: int | None
    out_label: int | None
    egress_if: str
    operation: "MPLSOperation | str"


@dataclass
class MPLSForwarder:
    """LFIB-driven MPLS forwarding behavior."""

    lfib: dict[int | None, LFIBEntry] = field(default_factory=dict)

    def install_entry(self, entry: LFIBEntry) -> None:
        key = entry.in_label
        self.lfib[key] = entry

    def forward(self, packet: PacketStack) -> tuple[str | None, PacketStack | None, str | None]:
        """Return (egress_if, packet_out, drop_reason) for MPLS pipeline."""
        top_label = next((h.label for h in packet.headers if isinstance(h, MPLSLabel)), None)
        entry = self.lfib.get(top_label)
        if entry is None and top_label is not None:
            return None, None, "no_lfib_entry"
        if entry is None:
            entry = self.lfib.get(None)
        if entry is None:
            return None, None, "no_lfib_entry"

        operation = MPLSOperation(entry.operation)

        if operation == MPLSOperation.PUSH:
            if entry.out_label is None:
                return None, None, "missing_out_label"
            out = self.push_label(packet, entry.out_label)
            return entry.egress_if, out, None

        if operation == MPLSOperation.SWAP:
            if entry.out_label is None:
                return None, None, "missing_out_label"
            out = packet.clone()
            for idx, header in enumerate(out.headers):
                if isinstance(header, MPLSLabel):
                    out.headers[idx] = replace(header, label=entry.out_label)
                    break
            return entry.egress_if, out, None

        if operation == MPLSOperation.POP:
            out = self.pop_label(packet)
            return entry.egress_if, out, None

        return None, None, "unsupported_operation"

    def push_label(self, packet: PacketStack, label: int) -> PacketStack:
        out = packet.clone()
        out.push_header(MPLSLabel(label=label, bottom_of_stack=not out.has_header(MPLSLabel)))
        return out

    def pop_label(self, packet: PacketStack) -> PacketStack:
        out = packet.clone()
        if not out.has_header(MPLSLabel):
            return out
        for idx, header in enumerate(out.headers):
            if isinstance(header, MPLSLabel):
                out.headers.pop(idx)
                return out
        return out
