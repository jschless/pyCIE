"""Packet model with explicit encapsulation stack operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

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
