"""Packet ID correlation helpers for telemetry."""

from __future__ import annotations

from itertools import count
from typing import Any

_PACKET_COUNTER = count(1)


def ensure_packet_id(frame_or_payload: Any) -> str:
    """Assign and return a stable packet ID."""
    packet_id = get_packet_id(frame_or_payload)
    if packet_id is not None:
        return packet_id

    packet_id = f"p{next(_PACKET_COUNTER)}"
    metadata = _metadata_dict(frame_or_payload)
    if metadata is not None:
        metadata["packet_id"] = packet_id
        return packet_id

    payload = getattr(frame_or_payload, "payload", None)
    payload_meta = _metadata_dict(payload)
    if payload_meta is not None:
        payload_meta["packet_id"] = packet_id
        return packet_id

    if hasattr(frame_or_payload, "__dict__"):
        setattr(frame_or_payload, "_packet_id", packet_id)
        return packet_id

    if payload is not None and hasattr(payload, "__dict__"):
        setattr(payload, "_packet_id", packet_id)
        return packet_id

    return packet_id


def get_packet_id(frame_or_payload: Any) -> str | None:
    """Read packet ID from metadata or fallback attribute."""
    metadata = _metadata_dict(frame_or_payload)
    if metadata is not None:
        packet_id = metadata.get("packet_id")
        if isinstance(packet_id, str) and packet_id:
            return packet_id

    payload = getattr(frame_or_payload, "payload", None)
    payload_meta = _metadata_dict(payload)
    if payload_meta is not None:
        packet_id = payload_meta.get("packet_id")
        if isinstance(packet_id, str) and packet_id:
            return packet_id

    packet_id = getattr(frame_or_payload, "_packet_id", None)
    if isinstance(packet_id, str) and packet_id:
        return packet_id

    payload_packet_id = getattr(payload, "_packet_id", None)
    if isinstance(payload_packet_id, str) and payload_packet_id:
        return payload_packet_id

    return None


def _metadata_dict(value: Any) -> dict[str, Any] | None:
    metadata = getattr(value, "metadata", None)
    if isinstance(metadata, dict):
        return metadata
    return None
