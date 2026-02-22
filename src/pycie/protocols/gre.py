"""Lab 11: GRE tunnel endpoint scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field

from pycie.forwarding.encapsulation import EncapsulationPipeline, TunnelConfig, TunnelMode
from pycie.model.headers import GREHeader, IPv4Header
from pycie.model.packet import PacketStack

from .base import ProtocolBase


@dataclass(frozen=True)
class GRETunnel:
    tunnel_id: str
    source_ip: str
    destination_ip: str
    key: int | None = None


@dataclass
class GRETunnelProcess(ProtocolBase):
    """GRE encapsulation/decapsulation endpoint logic.

    Reading:
    - RFC 2784
    - RFC 2890 (GRE key/sequence)
    """

    name: str = "gre"
    _pipeline: EncapsulationPipeline = field(default_factory=EncapsulationPipeline)
    _known_tunnels: dict[tuple[str, str, int | None], str] = field(default_factory=dict)

    def encapsulate(self, tunnel: GRETunnel, payload: PacketStack) -> PacketStack:
        """Return payload wrapped in GRE over IPv4."""
        self._known_tunnels[(tunnel.source_ip, tunnel.destination_ip, tunnel.key)] = tunnel.tunnel_id
        return self._pipeline.encapsulate(
            payload,
            TunnelConfig(
                tunnel_src=tunnel.source_ip,
                tunnel_dst=tunnel.destination_ip,
                mode=TunnelMode.GRE,
                key=tunnel.key,
            ),
        )

    def decapsulate(self, packet: PacketStack) -> tuple[str | None, PacketStack | None]:
        """Return (tunnel_id, inner_packet) when GRE packet matches tunnel."""
        if len(packet.headers) < 2:
            return None, None

        outer = packet.headers[0]
        gre = packet.headers[1]
        if not isinstance(outer, IPv4Header) or outer.protocol != 47:
            return None, None
        if not isinstance(gre, GREHeader):
            return None, None

        tunnel_key = (outer.src_ip, outer.dst_ip, gre.key)
        tunnel_id = self._known_tunnels.get(tunnel_key)
        if tunnel_id is None:
            tunnel_id = "default-gre"

        inner = self._pipeline.decapsulate(packet, TunnelMode.GRE)
        return tunnel_id, inner
