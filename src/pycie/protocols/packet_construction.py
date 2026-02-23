"""Lab 06a: packet construction and validation helpers."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from pycie.model.headers import Dot1QHeader, EthernetHeader, IPv4Header, TCPHeader, UDPHeader
from pycie.model.packet import PacketStack

from .base import ProtocolBase


@dataclass
class PacketConstructionProcess(ProtocolBase):
    """Build and validate deterministic packet header stacks."""

    name: str = "packet_construction"

    def build_packet(
        self,
        headers: list[Any],
        *,
        payload: bytes = b"",
        metadata: dict[str, Any] | None = None,
    ) -> PacketStack:
        """Build a packet and validate the outer->inner header order."""
        packet = PacketStack(headers=list(headers), payload=payload, metadata=dict(metadata or {}))
        valid, reason = packet.validate_stack_order()
        if not valid:
            raise ValueError(reason or "invalid_header_stack")
        return packet

    def build_ipv4_udp(
        self,
        *,
        src_mac: str,
        dst_mac: str,
        src_ip: str,
        dst_ip: str,
        src_port: int,
        dst_port: int,
        payload: bytes,
        dscp: int = 0,
    ) -> PacketStack:
        """Build Ethernet/IPv4/UDP packet with derived UDP length."""
        return self.build_packet(
            [
                EthernetHeader(dst_mac=dst_mac, src_mac=src_mac, ethertype="0x0800"),
                IPv4Header(src_ip=src_ip, dst_ip=dst_ip, dscp=dscp, protocol=17),
                UDPHeader(src_port=src_port, dst_port=dst_port, length=8 + len(payload)),
            ],
            payload=payload,
        )

    def build_ipv4_tcp(
        self,
        *,
        src_mac: str,
        dst_mac: str,
        src_ip: str,
        dst_ip: str,
        src_port: int,
        dst_port: int,
        flags: frozenset[str],
        payload: bytes = b"",
        dscp: int = 0,
    ) -> PacketStack:
        """Build Ethernet/IPv4/TCP packet with caller-provided flags."""
        return self.build_packet(
            [
                EthernetHeader(dst_mac=dst_mac, src_mac=src_mac, ethertype="0x0800"),
                IPv4Header(src_ip=src_ip, dst_ip=dst_ip, dscp=dscp, protocol=6),
                TCPHeader(src_port=src_port, dst_port=dst_port, flags=flags),
            ],
            payload=payload,
        )

    def insert_vlan_tag(self, packet: PacketStack, *, vlan_id: int, pcp: int = 0, dei: int = 0) -> PacketStack:
        """Insert an 802.1Q tag directly after the outer Ethernet header."""
        updated = packet.clone()
        if not updated.headers or not isinstance(updated.headers[0], EthernetHeader):
            raise ValueError("missing_outer_ethernet")

        updated.headers.insert(1, Dot1QHeader(vlan_id=vlan_id, pcp=pcp, dei=dei))
        valid, reason = updated.validate_stack_order()
        if not valid:
            raise ValueError(reason or "invalid_header_stack")
        return updated

    def normalize_transport_lengths(self, packet: PacketStack) -> PacketStack:
        """Normalize transport length fields based on payload size."""
        updated = packet.clone()
        payload_len = updated.compute_payload_length()

        for index, header in enumerate(updated.headers):
            if isinstance(header, UDPHeader):
                updated.headers[index] = replace(header, length=8 + payload_len)

        return updated

    def validate_packet(self, packet: PacketStack) -> tuple[bool, str | None]:
        """Expose packet-order validation for tests and explanations."""
        return packet.validate_stack_order()
