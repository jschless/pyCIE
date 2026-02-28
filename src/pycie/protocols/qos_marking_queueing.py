"""Lab 27: deterministic QoS marking and queue scheduling model."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from pycie.telemetry.events import EventType, Layer

from .base import ProtocolBase


@dataclass(frozen=True)
class QoSPacket:
    packet_id: str
    dscp: int
    size_bytes: int = 1


@dataclass
class QoSMarkingQueueingProcess(ProtocolBase):
    """Classify, mark, queue, and schedule packets with weighted fairness."""

    name: str = "qos_marking_queueing"
    queue_order: tuple[str, ...] = ("priority", "assured", "best_effort")
    queue_weights: dict[str, int] = field(default_factory=lambda: {"priority": 4, "assured": 2, "best_effort": 1})
    queue_limits: dict[str, int] = field(default_factory=lambda: {"priority": 32, "assured": 64, "best_effort": 128})
    queues: dict[str, list[QoSPacket]] = field(default_factory=dict)
    credits: dict[str, int] = field(default_factory=dict)
    cursor: int = 0

    def __post_init__(self) -> None:
        for queue in self.queue_order:
            self.queues.setdefault(queue, [])
            self.credits.setdefault(queue, 0)

    def classify_dscp(self, dscp: int) -> str:
        """Map DSCP values into deterministic output queues."""
        if dscp in {46, 48}:  # EF and CS6
            return "priority"
        if dscp in {10, 12, 14, 18, 20, 22, 26, 28, 30, 34, 36, 38}:
            return "assured"
        return "best_effort"

    def remark(self, packet: QoSPacket, *, new_dscp: int) -> QoSPacket:
        """Apply policy marking to a packet copy."""
        remarked = replace(packet, dscp=new_dscp)
        self.emit_trace(
            layer=Layer.L3,
            event_type=EventType.QOS_REMARK,
            packet_id=packet.packet_id,
            details={"old_dscp": packet.dscp, "new_dscp": new_dscp},
        )
        return remarked

    def enqueue(self, packet: QoSPacket) -> tuple[bool, str | None]:
        """Classify and enqueue packet, dropping when queue is full."""
        queue = self.classify_dscp(packet.dscp)
        limit = self.queue_limits.get(queue, 0)
        current = self.queues.setdefault(queue, [])
        if len(current) >= limit:
            self.emit_trace(
                layer=Layer.L3,
                event_type=EventType.QOS_ENQUEUE,
                packet_id=packet.packet_id,
                details={
                    "action": "drop",
                    "reason": "queue_full",
                    "queue": queue,
                    "depth": len(current),
                    "limit": limit,
                    "dscp": packet.dscp,
                },
            )
            return False, "queue_full"
        current.append(packet)
        self.emit_trace(
            layer=Layer.L3,
            event_type=EventType.QOS_ENQUEUE,
            packet_id=packet.packet_id,
            details={
                "action": "enqueue",
                "queue": queue,
                "depth": len(current),
                "limit": limit,
                "dscp": packet.dscp,
            },
        )
        return True, None

    def dequeue(self) -> QoSPacket | None:
        """Select next packet using weighted round-robin scheduling."""
        if not any(self.queues.get(queue) for queue in self.queue_order):
            return None

        queue_count = len(self.queue_order)
        for _ in range(queue_count * 3):
            queue = self.queue_order[self.cursor]
            packets = self.queues.setdefault(queue, [])

            if self.credits[queue] <= 0:
                self.credits[queue] = max(1, self.queue_weights.get(queue, 1))

            if packets:
                packet = packets.pop(0)
                self.credits[queue] -= 1
                if self.credits[queue] <= 0 or not packets:
                    self.cursor = (self.cursor + 1) % queue_count
                self.emit_trace(
                    layer=Layer.L3,
                    event_type=EventType.QOS_DEQUEUE,
                    packet_id=packet.packet_id,
                    details={
                        "queue": queue,
                        "remaining_depth": len(packets),
                        "dscp": packet.dscp,
                    },
                )
                return packet

            self.credits[queue] = 0
            self.cursor = (self.cursor + 1) % queue_count

        return None

    def queue_depth(self, queue: str) -> int:
        return len(self.queues.get(queue, []))

    def snapshot_depths(self) -> dict[str, int]:
        return {queue: len(self.queues.get(queue, [])) for queue in self.queue_order}
