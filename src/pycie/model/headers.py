"""Header definitions used by stack-based packet modeling."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EthernetHeader:
    dst_mac: str
    src_mac: str
    ethertype: str


@dataclass(frozen=True)
class Dot1QHeader:
    vlan_id: int
    pcp: int = 0
    dei: int = 0


@dataclass(frozen=True)
class IPv4Header:
    src_ip: str
    dst_ip: str
    ttl: int = 64
    dscp: int = 0
    protocol: int = 0


@dataclass(frozen=True)
class IPv6Header:
    src_ip: str
    dst_ip: str
    hop_limit: int = 64
    traffic_class: int = 0
    next_header: int = 0


@dataclass(frozen=True)
class UDPHeader:
    src_port: int
    dst_port: int
    length: int = 8
    checksum: int = 0


@dataclass(frozen=True)
class TCPHeader:
    src_port: int
    dst_port: int
    seq: int = 0
    ack: int = 0
    flags: frozenset[str] = frozenset()
    window: int = 65535
    checksum: int = 0


@dataclass(frozen=True)
class GREHeader:
    protocol_type: int
    key: int | None = None
    sequence: int | None = None


@dataclass(frozen=True)
class ESPHeader:
    spi: int
    sequence: int
    encrypted: bool = True


@dataclass(frozen=True)
class MPLSLabel:
    label: int
    exp: int = 0
    bottom_of_stack: bool = True
    ttl: int = 255
