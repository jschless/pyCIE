"""Packet/frame formatting helpers for richer visualization output."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any

from pycie.model.headers import Dot1QHeader, ESPHeader, EthernetHeader, GREHeader, IPv4Header, MPLSLabel
from pycie.model.packet import PacketStack


def frame_trace_details(frame: Any) -> dict[str, Any]:
    """Return JSON-serializable frame decode details for traces."""
    src_mac = _safe_getattr(frame, "src_mac")
    dst_mac = _safe_getattr(frame, "dst_mac")
    ethertype = _safe_getattr(frame, "ethertype")
    payload = _safe_getattr(frame, "payload")

    protocol_stack = _protocol_stack(payload)
    if src_mac is not None or dst_mac is not None:
        protocol_stack = ["EthernetII", *protocol_stack]

    details: dict[str, Any] = {}
    if isinstance(src_mac, str):
        details["src_mac"] = src_mac
    if isinstance(dst_mac, str):
        details["dst_mac"] = dst_mac
    if isinstance(ethertype, str):
        details["ethertype"] = ethertype

    details["protocol_stack"] = protocol_stack
    details["packet_summary"] = _frame_summary(src_mac, dst_mac, ethertype, payload)
    details["packet_tree"] = _frame_tree(src_mac, dst_mac, ethertype, payload)
    return details


def _frame_summary(src_mac: Any, dst_mac: Any, ethertype: Any, payload: Any) -> str:
    parts: list[str] = []

    if isinstance(src_mac, str) and isinstance(dst_mac, str):
        if isinstance(ethertype, str):
            parts.append(f"EthernetII {src_mac} -> {dst_mac} type={ethertype}")
        else:
            parts.append(f"EthernetII {src_mac} -> {dst_mac}")
    elif isinstance(ethertype, str):
        parts.append(f"EthernetII type={ethertype}")

    payload_summary = _payload_summary(payload)
    if payload_summary:
        parts.append(payload_summary)

    if not parts:
        return "Unknown frame"
    return " | ".join(parts)


def _payload_summary(payload: Any) -> str:
    if isinstance(payload, PacketStack):
        header_parts = [_header_summary(header) for header in payload.headers]
        if payload.payload:
            header_parts.append(f"Payload[{len(payload.payload)}B]")
        return " / ".join(part for part in header_parts if part)

    if _is_ip_packet(payload):
        src_ip = _safe_getattr(payload, "src_ip")
        dst_ip = _safe_getattr(payload, "dst_ip")
        proto = _safe_getattr(payload, "protocol")
        return f"IPv4 {src_ip} -> {dst_ip} proto={proto}"

    if isinstance(payload, (bytes, bytearray)):
        return f"Payload[{len(payload)}B]"

    if payload is None:
        return ""
    return payload.__class__.__name__


def _frame_tree(src_mac: Any, dst_mac: Any, ethertype: Any, payload: Any) -> list[str]:
    lines: list[str] = ["Ethernet II"]
    if isinstance(src_mac, str):
        lines.append(f"  src_mac: {src_mac}")
    if isinstance(dst_mac, str):
        lines.append(f"  dst_mac: {dst_mac}")
    if isinstance(ethertype, str):
        lines.append(f"  ethertype: {ethertype}")

    lines.append("  payload:")
    payload_tree = _payload_tree(payload)
    for line in payload_tree:
        lines.append(f"    {line}")
    return lines


def _payload_tree(payload: Any) -> list[str]:
    if isinstance(payload, PacketStack):
        lines = ["PacketStack"]
        for idx, header in enumerate(payload.headers):
            lines.extend(_indent(_header_tree(idx, header), 2))
        if payload.payload:
            lines.append(f"  payload_bytes: {len(payload.payload)}")
        else:
            lines.append("  payload_bytes: 0")
        if payload.metadata:
            lines.append("  metadata:")
            for key in sorted(payload.metadata):
                lines.append(f"    {key}: {payload.metadata[key]}")
        return lines

    if _is_ip_packet(payload):
        src_ip = _safe_getattr(payload, "src_ip")
        dst_ip = _safe_getattr(payload, "dst_ip")
        proto = _safe_getattr(payload, "protocol")
        return [
            "IPv4 Packet",
            f"  src_ip: {src_ip}",
            f"  dst_ip: {dst_ip}",
            f"  protocol: {proto}",
        ]

    if isinstance(payload, (bytes, bytearray)):
        return [f"Raw bytes ({len(payload)} bytes)"]

    if payload is None:
        return ["(none)"]

    return [payload.__class__.__name__]


def _header_summary(header: Any) -> str:
    if isinstance(header, EthernetHeader):
        return f"EthernetII({header.src_mac}->{header.dst_mac},type={header.ethertype})"
    if isinstance(header, Dot1QHeader):
        return f"802.1Q(vlan={header.vlan_id},pcp={header.pcp})"
    if isinstance(header, IPv4Header):
        return f"IPv4({header.src_ip}->{header.dst_ip},ttl={header.ttl},proto={header.protocol})"
    if isinstance(header, GREHeader):
        key = f",key={header.key}" if header.key is not None else ""
        return f"GRE(proto=0x{header.protocol_type:04x}{key})"
    if isinstance(header, ESPHeader):
        return f"ESP(spi={header.spi},seq={header.sequence})"
    if isinstance(header, MPLSLabel):
        bos = 1 if header.bottom_of_stack else 0
        return f"MPLS(label={header.label},ttl={header.ttl},bos={bos})"
    if is_dataclass(header):
        field_repr = ", ".join(f"{f.name}={getattr(header, f.name)!r}" for f in fields(header))
        return f"{header.__class__.__name__}({field_repr})"
    return header.__class__.__name__


def _header_tree(index: int, header: Any) -> list[str]:
    lines = [f"header[{index}]: {_header_name(header)}"]
    if is_dataclass(header):
        for field_obj in fields(header):
            lines.append(f"  {field_obj.name}: {getattr(header, field_obj.name)}")
    else:
        lines.append(f"  value: {header}")
    return lines


def _header_name(header: Any) -> str:
    if isinstance(header, EthernetHeader):
        return "Ethernet II"
    if isinstance(header, Dot1QHeader):
        return "802.1Q"
    if isinstance(header, IPv4Header):
        return "IPv4"
    if isinstance(header, GREHeader):
        return "GRE"
    if isinstance(header, ESPHeader):
        return "ESP"
    if isinstance(header, MPLSLabel):
        return "MPLS"
    return header.__class__.__name__


def _protocol_stack(payload: Any) -> list[str]:
    if isinstance(payload, PacketStack):
        return [_header_name(header).replace(" ", "") for header in payload.headers]
    if _is_ip_packet(payload):
        return ["IPv4"]
    return []


def _indent(lines: list[str], level: int) -> list[str]:
    prefix = " " * level
    return [f"{prefix}{line}" for line in lines]


def _is_ip_packet(payload: Any) -> bool:
    return (
        _safe_getattr(payload, "src_ip") is not None
        and _safe_getattr(payload, "dst_ip") is not None
        and _safe_getattr(payload, "protocol") is not None
    )


def _safe_getattr(obj: Any, name: str) -> Any:
    try:
        return getattr(obj, name)
    except Exception:
        return None
