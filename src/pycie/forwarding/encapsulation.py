"""Encapsulation pipeline scaffold for GRE/IPsec/MPLS exercises."""

from __future__ import annotations

from dataclasses import dataclass

from pycie.model.headers import ESPHeader, GREHeader, IPv4Header
from pycie.model.packet import PacketStack


@dataclass(frozen=True)
class TunnelConfig:
    tunnel_src: str
    tunnel_dst: str
    mode: str  # gre | ipip | ipsec
    key: int | None = None
    ipsec_spi: int | None = None


class EncapsulationPipeline:
    """Header-stack transformations for tunnel encapsulation."""

    def encapsulate(self, packet: PacketStack, config: TunnelConfig) -> PacketStack:
        """Return new packet with tunnel headers pushed."""
        if config.mode == "gre":
            return self._push_gre(packet, config)
        if config.mode == "ipsec":
            return self._push_ipsec(packet, config)
        if config.mode == "ipip":
            out = packet.clone()
            out.push_header(IPv4Header(src_ip=config.tunnel_src, dst_ip=config.tunnel_dst, protocol=4))
            return out
        raise ValueError(f"unsupported tunnel mode {config.mode!r}")

    def decapsulate(self, packet: PacketStack, mode: str) -> PacketStack:
        """Return packet with expected outer tunnel headers removed."""
        out = packet.clone()

        if mode == "gre":
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

        if mode == "ipsec":
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

        if mode == "ipip":
            if out.headers and isinstance(out.headers[0], IPv4Header) and out.headers[0].protocol == 4:
                out.headers = out.headers[1:]
            return out

        raise ValueError(f"unsupported tunnel mode {mode!r}")

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
