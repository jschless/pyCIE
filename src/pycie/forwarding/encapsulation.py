"""Encapsulation pipeline scaffold for GRE/IPsec/MPLS exercises."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from pycie.model.headers import ESPHeader, GREHeader, IPv4Header
from pycie.model.packet import PacketStack


class TunnelMode(StrEnum):
    GRE = "gre"
    IPIP = "ipip"
    IPSEC = "ipsec"


@dataclass(frozen=True)
class TunnelConfig:
    tunnel_src: str
    tunnel_dst: str
    mode: "TunnelMode | str"
    key: int | None = None
    ipsec_spi: int | None = None


class EncapsulationPipeline:
    """Header-stack transformations for tunnel encapsulation."""

    def encapsulate(self, packet: PacketStack, config: TunnelConfig) -> PacketStack:
        """Return new packet with tunnel headers pushed."""
        mode = TunnelMode(config.mode)
        if mode == TunnelMode.GRE:
            return self._push_gre(packet, config)
        if mode == TunnelMode.IPSEC:
            return self._push_ipsec(packet, config)
        if mode == TunnelMode.IPIP:
            out = packet.clone()
            out.push_header(IPv4Header(src_ip=config.tunnel_src, dst_ip=config.tunnel_dst, protocol=4))
            return out
        raise ValueError(f"unsupported tunnel mode {mode!r}")

    def decapsulate(self, packet: PacketStack, mode: "TunnelMode | str") -> PacketStack:
        """Return packet with expected outer tunnel headers removed."""
        out = packet.clone()
        tunnel_mode = TunnelMode(mode)

        if tunnel_mode == TunnelMode.GRE:
            if len(out.headers) < 2:
                return out
            if not isinstance(out.headers[0], IPv4Header):
                return out
            if out.headers[0].protocol != 47:
                return out
            if not isinstance(out.headers[1], GREHeader):
                return out
            out.headers = out.headers[2:]
            return out

        if tunnel_mode == TunnelMode.IPSEC:
            if len(out.headers) < 2:
                return out
            if not isinstance(out.headers[0], IPv4Header):
                return out
            if out.headers[0].protocol != 50:
                return out
            if not isinstance(out.headers[1], ESPHeader):
                return out
            out.headers = out.headers[2:]
            return out

        if tunnel_mode == TunnelMode.IPIP:
            if out.headers and isinstance(out.headers[0], IPv4Header) and out.headers[0].protocol == 4:
                out.headers = out.headers[1:]
            return out

        raise ValueError(f"unsupported tunnel mode {tunnel_mode!r}")

    def _push_gre(self, packet: PacketStack, config: TunnelConfig) -> PacketStack:
        out = packet.clone()
        out.push_header(GREHeader(protocol_type=0x0800, key=config.key))
        out.push_header(IPv4Header(src_ip=config.tunnel_src, dst_ip=config.tunnel_dst, protocol=47))
        return out

    def _push_ipsec(self, packet: PacketStack, config: TunnelConfig) -> PacketStack:
        out = packet.clone()
        out.push_header(ESPHeader(spi=config.ipsec_spi or 1, sequence=1, encrypted=True))
        out.push_header(IPv4Header(src_ip=config.tunnel_src, dst_ip=config.tunnel_dst, protocol=50))
        return out
