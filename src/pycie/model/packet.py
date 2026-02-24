"""Packet model with explicit encapsulation stack operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pycie.model.headers import (
    Dot1QHeader,
    EthernetHeader,
    ESPHeader,
    GREHeader,
    ICMPHeader,
    ICMPv6Header,
    IPv4Header,
    IPv6Header,
    MPLSLabel,
    TCPHeader,
    UDPHeader,
)

Header = Any


@dataclass
class PacketStack:
    """A packet represented as an ordered list of headers + payload.

    The first header in `headers` is the outermost encapsulation.
    """

    headers: list[Header] = field(default_factory=list)
    payload: bytes = b""
    metadata: dict[str, Any] = field(default_factory=dict)

    def push_header(self, header: Header) -> None:
        """Push a new outer header."""
        self.headers.insert(0, header)

    def append_inner_header(self, header: Header) -> None:
        """Append a deeper header below current stack."""
        self.headers.append(header)

    def pop_header(self) -> Header:
        """Pop and return the current outer header."""
        if not self.headers:
            raise IndexError("no headers to pop")
        return self.headers.pop(0)

    def peek_header(self) -> Header | None:
        """Return the current outer header without mutation."""
        if not self.headers:
            return None
        return self.headers[0]

    def has_header(self, header_type: type[Any]) -> bool:
        """Return True if any header in stack is instance of type."""
        return any(isinstance(h, header_type) for h in self.headers)

    def clone(self) -> "PacketStack":
        """Return a shallow clone preserving header order."""
        return PacketStack(
            headers=list(self.headers),
            payload=self.payload,
            metadata=dict(self.metadata),
        )

    def compute_payload_length(self) -> int:
        """Return payload length in bytes."""
        return len(self.payload)

    def validate_stack_order(self) -> tuple[bool, str | None]:
        """Validate deterministic outer->inner header ordering rules."""
        if not self.headers:
            return False, "no_headers"

        previous_rank = -1
        saw_l3 = False
        for index, header in enumerate(self.headers):
            rank = _header_rank(header)
            if rank < previous_rank:
                return False, f"invalid_order_at_index_{index}"
            previous_rank = rank

            if isinstance(header, Dot1QHeader):
                if index == 0 or not isinstance(self.headers[index - 1], EthernetHeader):
                    return False, "dot1q_without_outer_ethernet"

            if isinstance(header, (IPv4Header, IPv6Header)):
                saw_l3 = True

            if isinstance(header, (TCPHeader, UDPHeader, ICMPHeader, ICMPv6Header)) and not saw_l3:
                return False, "l4_without_l3"

        return True, None


def _header_rank(header: Header) -> int:
    if isinstance(header, EthernetHeader):
        return 0
    if isinstance(header, Dot1QHeader):
        return 1
    if isinstance(header, MPLSLabel):
        return 2
    if isinstance(header, (IPv4Header, IPv6Header)):
        return 3
    if isinstance(header, (GREHeader, ESPHeader)):
        return 4
    if isinstance(header, (TCPHeader, UDPHeader)):
        return 5
    if isinstance(header, (ICMPHeader, ICMPv6Header)):
        return 5
    return 99
