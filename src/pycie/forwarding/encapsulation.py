"""Encapsulation pipeline scaffold for GRE/IPsec/MPLS exercises."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from pycie.model.headers import ESPHeader, GREHeader, IPv4Header
from pycie.model.packet import PacketStack
from pycie.telemetry.events import EventType, Layer
from pycie.telemetry.packet import ensure_packet_id
from pycie.telemetry.trace import emit_from_env


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

    def __init__(self, *, trace_node: str = "encapsulation") -> None:
        self.trace_node = trace_node

    def encapsulate(self, packet: PacketStack, config: TunnelConfig) -> PacketStack:
        """Return new packet with tunnel headers pushed."""
        packet_id = ensure_packet_id(packet)
        inner_proto = self._header_name(packet)
        mode = TunnelMode(config.mode)
        if mode == TunnelMode.GRE:
            out = self._push_gre(packet, config)
            self._emit_trace(
                event_type=EventType.ENCAP_PUSH,
                packet_id=packet_id,
                details={
                    "outer_proto": self._header_name(out),
                    "inner_proto": inner_proto,
                    "tunnel_type": TunnelMode.GRE.value,
                },
            )
            return out
        if mode == TunnelMode.IPSEC:
            out = self._push_ipsec(packet, config)
            self._emit_trace(
                event_type=EventType.CRYPTO_ENCRYPT,
                packet_id=packet_id,
                details={
                    "transform": "esp",
                    "mode": "tunnel",
                    "spi": config.ipsec_spi or 1,
                },
            )
            self._emit_trace(
                event_type=EventType.ENCAP_PUSH,
                packet_id=packet_id,
                details={
                    "outer_proto": self._header_name(out),
                    "inner_proto": inner_proto,
                    "tunnel_type": TunnelMode.IPSEC.value,
                },
            )
            return out
        if mode == TunnelMode.IPIP:
            out = packet.clone()
            out.push_header(IPv4Header(src_ip=config.tunnel_src, dst_ip=config.tunnel_dst, protocol=4))
            self._emit_trace(
                event_type=EventType.ENCAP_PUSH,
                packet_id=packet_id,
                details={
                    "outer_proto": self._header_name(out),
                    "inner_proto": inner_proto,
                    "tunnel_type": TunnelMode.IPIP.value,
                },
            )
            return out
        raise ValueError(f"unsupported tunnel mode {mode!r}")

    def decapsulate(self, packet: PacketStack, mode: "TunnelMode | str") -> PacketStack:
        """Return packet with expected outer tunnel headers removed."""
        out = packet.clone()
        packet_id = ensure_packet_id(out)
        outer_proto = self._header_name(out)
        tunnel_mode = TunnelMode(mode)

        if tunnel_mode == TunnelMode.GRE:
            if len(out.headers) < 2:
                self._emit_trace(
                    event_type=EventType.FRAME_DROP,
                    packet_id=packet_id,
                    details={"drop_reason": "gre_truncated"},
                )
                return out
            if not isinstance(out.headers[0], IPv4Header):
                self._emit_trace(
                    event_type=EventType.FRAME_DROP,
                    packet_id=packet_id,
                    details={"drop_reason": "gre_missing_outer_ipv4"},
                )
                return out
            if out.headers[0].protocol != 47:
                self._emit_trace(
                    event_type=EventType.FRAME_DROP,
                    packet_id=packet_id,
                    details={"drop_reason": "gre_wrong_ipv4_protocol"},
                )
                return out
            if not isinstance(out.headers[1], GREHeader):
                self._emit_trace(
                    event_type=EventType.FRAME_DROP,
                    packet_id=packet_id,
                    details={"drop_reason": "gre_header_missing"},
                )
                return out
            out.headers = out.headers[2:]
            self._emit_trace(
                event_type=EventType.ENCAP_POP,
                packet_id=packet_id,
                details={
                    "outer_proto": outer_proto,
                    "inner_proto": self._header_name(out),
                    "tunnel_type": TunnelMode.GRE.value,
                },
            )
            return out

        if tunnel_mode == TunnelMode.IPSEC:
            if len(out.headers) < 2:
                self._emit_trace(
                    event_type=EventType.FRAME_DROP,
                    packet_id=packet_id,
                    details={"drop_reason": "ipsec_truncated"},
                )
                return out
            if not isinstance(out.headers[0], IPv4Header):
                self._emit_trace(
                    event_type=EventType.FRAME_DROP,
                    packet_id=packet_id,
                    details={"drop_reason": "ipsec_missing_outer_ipv4"},
                )
                return out
            if out.headers[0].protocol != 50:
                self._emit_trace(
                    event_type=EventType.FRAME_DROP,
                    packet_id=packet_id,
                    details={"drop_reason": "ipsec_wrong_ipv4_protocol"},
                )
                return out
            if not isinstance(out.headers[1], ESPHeader):
                self._emit_trace(
                    event_type=EventType.FRAME_DROP,
                    packet_id=packet_id,
                    details={"drop_reason": "esp_header_missing"},
                )
                return out
            esp = out.headers[1]
            self._emit_trace(
                event_type=EventType.CRYPTO_DECRYPT,
                packet_id=packet_id,
                details={
                    "transform": "esp",
                    "mode": "tunnel",
                    "spi": esp.spi,
                },
            )
            out.headers = out.headers[2:]
            self._emit_trace(
                event_type=EventType.ENCAP_POP,
                packet_id=packet_id,
                details={
                    "outer_proto": outer_proto,
                    "inner_proto": self._header_name(out),
                    "tunnel_type": TunnelMode.IPSEC.value,
                },
            )
            return out

        if tunnel_mode == TunnelMode.IPIP:
            if out.headers and isinstance(out.headers[0], IPv4Header) and out.headers[0].protocol == 4:
                out.headers = out.headers[1:]
                self._emit_trace(
                    event_type=EventType.ENCAP_POP,
                    packet_id=packet_id,
                    details={
                        "outer_proto": outer_proto,
                        "inner_proto": self._header_name(out),
                        "tunnel_type": TunnelMode.IPIP.value,
                    },
                )
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

    def _emit_trace(
        self,
        *,
        event_type: EventType,
        packet_id: str | None,
        details: dict[str, object],
    ) -> None:
        emit_from_env(
            sim_time_ms=0,
            node=self.trace_node,
            layer=(
                Layer.TUNNEL
                if event_type in {EventType.ENCAP_PUSH, EventType.ENCAP_POP, EventType.FRAME_DROP}
                else Layer.CRYPTO
            ),
            event_type=event_type,
            packet_id=packet_id,
            details=details,
        )

    @staticmethod
    def _header_name(packet: PacketStack) -> str:
        if not packet.headers:
            return "payload"
        return type(packet.headers[0]).__name__
