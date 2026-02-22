"""Forwarding Information Base (FIB) scaffold."""

from __future__ import annotations

from dataclasses import dataclass

from .rib import RIB


@dataclass(frozen=True)
class ForwardingEntry:
    """Active forwarding entry derived from best routes."""

    prefix: str
    next_hop: str | None
    outgoing_interface: str | None = None


class FIB:
    """Simple FIB projection from a RIB."""

    def __init__(self) -> None:
        self._entries: dict[str, ForwardingEntry] = {}

    def recompute(self, rib: RIB) -> None:
        self._entries.clear()
        for prefix, route in rib.all_best_routes().items():
            self._entries[prefix] = ForwardingEntry(
                prefix=prefix,
                next_hop=route.next_hop,
                outgoing_interface=route.attributes.get("outgoing_interface"),
            )

    def lookup(self, prefix: str) -> ForwardingEntry | None:
        return self._entries.get(prefix)

    def entries(self) -> dict[str, ForwardingEntry]:
        return dict(self._entries)
