"""Typed telemetry event schema for pyCIE trace output."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


SCHEMA_VERSION = 1


class Layer(StrEnum):
    """Supported telemetry layers for visualization and filtering."""

    SIM = "SIM"
    L2 = "L2"
    STP = "STP"
    L3 = "L3"
    TUNNEL = "TUNNEL"
    CRYPTO = "CRYPTO"


class EventType(StrEnum):
    """Canonical telemetry event names."""

    FRAME_ENQUEUE = "FRAME_ENQUEUE"
    FRAME_DELIVER = "FRAME_DELIVER"
    FRAME_DROP = "FRAME_DROP"
    FRAME_RX = "FRAME_RX"
    FRAME_TX = "FRAME_TX"

    MAC_LEARN = "MAC_LEARN"
    MAC_AGE_OUT = "MAC_AGE_OUT"
    L2_FLOOD = "L2_FLOOD"
    L2_UNICAST_FORWARD = "L2_UNICAST_FORWARD"

    STP_BPDU_TX = "STP_BPDU_TX"
    STP_BPDU_RX = "STP_BPDU_RX"
    STP_ROOT_CHANGE = "STP_ROOT_CHANGE"
    STP_PORT_ROLE_CHANGE = "STP_PORT_ROLE_CHANGE"

    ROUTE_LOOKUP = "ROUTE_LOOKUP"
    ROUTE_SELECT = "ROUTE_SELECT"
    FIB_FORWARD = "FIB_FORWARD"
    FIB_DROP = "FIB_DROP"

    ENCAP_PUSH = "ENCAP_PUSH"
    ENCAP_POP = "ENCAP_POP"
    CRYPTO_ENCRYPT = "CRYPTO_ENCRYPT"
    CRYPTO_DECRYPT = "CRYPTO_DECRYPT"


@dataclass(frozen=True)
class TraceEvent:
    """One normalized trace event."""

    schema_version: int
    seq: int
    ts_ms: int
    sim_time_ms: int
    node: str
    ingress_if: str | None = None
    egress_if: str | None = None
    packet_id: str | None = None
    layer: Layer = Layer.SIM
    event_type: EventType = EventType.FRAME_ENQUEUE
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema_version <= 0:
            raise ValueError("schema_version must be positive")
        if self.seq <= 0:
            raise ValueError("seq must be positive")
        if not self.node:
            raise ValueError("node must be non-empty")
        if self.ingress_if is not None and not self.ingress_if:
            raise ValueError("ingress_if must be non-empty when provided")
        if self.egress_if is not None and not self.egress_if:
            raise ValueError("egress_if must be non-empty when provided")
        if self.packet_id is not None and not self.packet_id:
            raise ValueError("packet_id must be non-empty when provided")

    def to_dict(self) -> dict[str, Any]:
        """Serialize event as JSON-compatible dictionary."""
        return {
            "schema_version": self.schema_version,
            "seq": self.seq,
            "ts_ms": self.ts_ms,
            "sim_time_ms": self.sim_time_ms,
            "node": self.node,
            "ingress_if": self.ingress_if,
            "egress_if": self.egress_if,
            "packet_id": self.packet_id,
            "layer": self.layer.value,
            "event_type": self.event_type.value,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "TraceEvent":
        """Deserialize and validate event from dictionary."""
        details = raw.get("details", {})
        if not isinstance(details, dict):
            raise ValueError("details must be a dictionary")
        for key in details:
            if not isinstance(key, str):
                raise ValueError("details keys must be strings")

        try:
            layer = Layer(str(raw["layer"]))
        except KeyError as exc:  # pragma: no cover
            raise ValueError("layer is required") from exc
        except ValueError as exc:
            raise ValueError(f"unknown layer {raw.get('layer')!r}") from exc

        try:
            event_type = EventType(str(raw["event_type"]))
        except KeyError as exc:  # pragma: no cover
            raise ValueError("event_type is required") from exc
        except ValueError as exc:
            raise ValueError(f"unknown event_type {raw.get('event_type')!r}") from exc

        node = raw.get("node")
        if not isinstance(node, str):
            raise ValueError("node must be a string")

        ingress_if = raw.get("ingress_if")
        if ingress_if is not None and not isinstance(ingress_if, str):
            raise ValueError("ingress_if must be a string or null")

        egress_if = raw.get("egress_if")
        if egress_if is not None and not isinstance(egress_if, str):
            raise ValueError("egress_if must be a string or null")

        packet_id = raw.get("packet_id")
        if packet_id is not None and not isinstance(packet_id, str):
            raise ValueError("packet_id must be a string or null")

        return cls(
            schema_version=int(raw["schema_version"]),
            seq=int(raw["seq"]),
            ts_ms=int(raw["ts_ms"]),
            sim_time_ms=int(raw["sim_time_ms"]),
            node=node,
            ingress_if=ingress_if,
            egress_if=egress_if,
            packet_id=packet_id,
            layer=layer,
            event_type=event_type,
            details=details,
        )
