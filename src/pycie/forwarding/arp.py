"""ARP cache and pending resolution queue scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field

from pycie.model.packet import PacketStack


@dataclass(frozen=True)
class ARPEntry:
    ip: str
    mac: str
    learned_at_ms: float
    ttl_ms: int = 240_000


@dataclass(frozen=True)
class PendingPacket:
    next_hop_ip: str
    packet: PacketStack
    enqueued_at_ms: float


@dataclass
class ARPTable:
    """IP-to-MAC cache with queue for unresolved next-hop packets."""

    entries: dict[str, ARPEntry] = field(default_factory=dict)
    pending: dict[str, list[PendingPacket]] = field(default_factory=dict)

    def lookup(self, ip: str, now_ms: float) -> str | None:
        """Return MAC if entry is present and not expired."""
        entry = self.entries.get(ip)
        if entry is None:
            return None
        if now_ms - entry.learned_at_ms >= entry.ttl_ms:
            del self.entries[ip]
            return None
        return entry.mac

    def update(self, ip: str, mac: str, now_ms: float, ttl_ms: int = 240_000) -> None:
        """Install or refresh ARP cache entry."""
        self.entries[ip] = ARPEntry(ip=ip, mac=mac, learned_at_ms=now_ms, ttl_ms=ttl_ms)

    def enqueue_pending(self, next_hop_ip: str, packet: PacketStack, now_ms: float) -> None:
        """Queue packet while waiting for ARP resolution."""
        self.pending.setdefault(next_hop_ip, []).append(
            PendingPacket(
                next_hop_ip=next_hop_ip,
                packet=packet.clone(),
                enqueued_at_ms=now_ms,
            )
        )

    def drain_pending(self, next_hop_ip: str) -> list[PacketStack]:
        """Pop queued packets for next-hop after resolution."""
        packets = self.pending.pop(next_hop_ip, [])
        return [pending.packet for pending in packets]

    def needs_request(self, next_hop_ip: str, now_ms: float) -> bool:
        """Return True if ARP request should be emitted for next hop."""
        return self.lookup(next_hop_ip, now_ms) is None

    def age(self, now_ms: float) -> None:
        """Expire stale ARP entries."""
        expired = [
            ip
            for ip, entry in self.entries.items()
            if now_ms - entry.learned_at_ms >= entry.ttl_ms
        ]
        for ip in expired:
            del self.entries[ip]
