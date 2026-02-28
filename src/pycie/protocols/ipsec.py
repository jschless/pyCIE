"""Lab 12: IPsec tunnel-mode scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from ipaddress import ip_address, ip_network

from pycie.model.headers import ESPHeader, IPv4Header
from pycie.model.packet import PacketStack
from pycie.telemetry.events import EventType, Layer
from pycie.telemetry.packet import ensure_packet_id

from .base import ProtocolBase


class IPSecMode(StrEnum):
    TUNNEL = "tunnel"


class IPSecPolicyAction(StrEnum):
    PROTECT = "protect"
    BYPASS = "bypass"
    DROP = "drop"


@dataclass(frozen=True)
class SecurityAssociation:
    spi: int
    src_ip: str
    dst_ip: str
    mode: "IPSecMode | str" = IPSecMode.TUNNEL
    encryption: str = "aes-gcm"
    auth: str = "sha256"


@dataclass(frozen=True)
class SecurityPolicy:
    policy_id: str
    src_prefix: str
    dst_prefix: str
    action: "IPSecPolicyAction | str"
    sa_spi: int | None = None


@dataclass
class IPsecProcess(ProtocolBase):
    """Simplified SPD/SAD processing for tunnel mode.

    Reading:
    - RFC 4301
    - RFC 4303
    """

    name: str = "ipsec"
    sad: dict[int, SecurityAssociation] = field(default_factory=dict)
    spd: list[SecurityPolicy] = field(default_factory=list)

    def install_sa(self, sa: SecurityAssociation) -> None:
        self.sad[sa.spi] = sa

    def install_policy(self, policy: SecurityPolicy) -> None:
        self.spd.append(policy)

    def outbound(self, packet: PacketStack) -> tuple["IPSecPolicyAction | str", PacketStack | None]:
        """Return (action, packet_or_none) after SPD/SAD outbound processing."""
        packet_id = ensure_packet_id(packet)
        ip_header = next((h for h in packet.headers if isinstance(h, IPv4Header)), None)
        if ip_header is None:
            self.emit_trace(
                layer=Layer.CRYPTO,
                event_type=EventType.FRAME_DROP,
                packet_id=packet_id,
                details={"drop_reason": "no_ipv4_header"},
            )
            return IPSecPolicyAction.DROP, None

        policy = self._match_policy(ip_header.src_ip, ip_header.dst_ip)
        if policy is None:
            self.emit_trace(
                layer=Layer.CRYPTO,
                event_type=EventType.IPSEC_POLICY_EVALUATE,
                packet_id=packet_id,
                details={
                    "direction": "outbound",
                    "action": IPSecPolicyAction.BYPASS.value,
                    "reason": "no_policy_match",
                    "src_ip": ip_header.src_ip,
                    "dst_ip": ip_header.dst_ip,
                },
            )
            return IPSecPolicyAction.BYPASS, packet.clone()

        action = IPSecPolicyAction(policy.action)
        if action == IPSecPolicyAction.DROP:
            self.emit_trace(
                layer=Layer.CRYPTO,
                event_type=EventType.IPSEC_POLICY_EVALUATE,
                packet_id=packet_id,
                details={
                    "direction": "outbound",
                    "action": action.value,
                    "policy_id": policy.policy_id,
                    "reason": "policy_drop",
                    "src_ip": ip_header.src_ip,
                    "dst_ip": ip_header.dst_ip,
                },
            )
            self.emit_trace(
                layer=Layer.CRYPTO,
                event_type=EventType.FRAME_DROP,
                packet_id=packet_id,
                details={"drop_reason": "policy_drop", "policy_id": policy.policy_id},
            )
            return IPSecPolicyAction.DROP, None
        if action == IPSecPolicyAction.BYPASS:
            self.emit_trace(
                layer=Layer.CRYPTO,
                event_type=EventType.IPSEC_POLICY_EVALUATE,
                packet_id=packet_id,
                details={
                    "direction": "outbound",
                    "action": action.value,
                    "policy_id": policy.policy_id,
                    "reason": "policy_bypass",
                    "src_ip": ip_header.src_ip,
                    "dst_ip": ip_header.dst_ip,
                },
            )
            return IPSecPolicyAction.BYPASS, packet.clone()
        self.emit_trace(
            layer=Layer.CRYPTO,
            event_type=EventType.IPSEC_POLICY_EVALUATE,
            packet_id=packet_id,
            details={
                "direction": "outbound",
                "action": action.value,
                "policy_id": policy.policy_id,
                "reason": "policy_protect",
                "src_ip": ip_header.src_ip,
                "dst_ip": ip_header.dst_ip,
            },
        )

        if policy.sa_spi is None:
            self.emit_trace(
                layer=Layer.CRYPTO,
                event_type=EventType.IPSEC_SA_LOOKUP,
                packet_id=packet_id,
                details={
                    "direction": "outbound",
                    "spi": None,
                    "result": "missing_spi",
                    "policy_id": policy.policy_id,
                },
            )
            self.emit_trace(
                layer=Layer.CRYPTO,
                event_type=EventType.FRAME_DROP,
                packet_id=packet_id,
                details={"drop_reason": "missing_sa_spi", "policy_id": policy.policy_id},
            )
            return IPSecPolicyAction.DROP, None
        sa = self.sad.get(policy.sa_spi)
        if sa is None:
            self.emit_trace(
                layer=Layer.CRYPTO,
                event_type=EventType.IPSEC_SA_LOOKUP,
                packet_id=packet_id,
                details={
                    "direction": "outbound",
                    "spi": policy.sa_spi,
                    "result": "miss",
                    "policy_id": policy.policy_id,
                },
            )
            self.emit_trace(
                layer=Layer.CRYPTO,
                event_type=EventType.FRAME_DROP,
                packet_id=packet_id,
                details={"drop_reason": "sa_not_found", "spi": policy.sa_spi},
            )
            return IPSecPolicyAction.DROP, None
        self.emit_trace(
            layer=Layer.CRYPTO,
            event_type=EventType.IPSEC_SA_LOOKUP,
            packet_id=packet_id,
            details={
                "direction": "outbound",
                "spi": sa.spi,
                "result": "hit",
                "policy_id": policy.policy_id,
            },
        )

        protected = packet.clone()
        protected.push_header(ESPHeader(spi=sa.spi, sequence=1, encrypted=True))
        protected.push_header(IPv4Header(src_ip=sa.src_ip, dst_ip=sa.dst_ip, protocol=50))
        self.emit_trace(
            layer=Layer.CRYPTO,
            event_type=EventType.CRYPTO_ENCRYPT,
            packet_id=packet_id,
            details={
                "transform": "esp",
                "mode": IPSecMode(sa.mode).value,
                "spi": sa.spi,
            },
        )
        self.emit_trace(
            layer=Layer.TUNNEL,
            event_type=EventType.ENCAP_PUSH,
            packet_id=packet_id,
            details={
                "outer_proto": "IPv4Header",
                "inner_proto": type(packet.headers[0]).__name__ if packet.headers else "payload",
                "tunnel_type": "ipsec",
            },
        )
        return IPSecPolicyAction.PROTECT, protected

    def inbound(self, packet: PacketStack) -> tuple["IPSecPolicyAction | str", PacketStack | None]:
        """Return (action, packet_or_none) after inbound ESP processing."""
        packet_id = ensure_packet_id(packet)
        if not packet.headers:
            self.emit_trace(
                layer=Layer.CRYPTO,
                event_type=EventType.FRAME_DROP,
                packet_id=packet_id,
                details={"drop_reason": "empty_packet"},
            )
            return IPSecPolicyAction.DROP, None

        outer = packet.headers[0]
        if not isinstance(outer, IPv4Header) or outer.protocol != 50:
            self.emit_trace(
                layer=Layer.CRYPTO,
                event_type=EventType.IPSEC_POLICY_EVALUATE,
                packet_id=packet_id,
                details={
                    "direction": "inbound",
                    "action": IPSecPolicyAction.BYPASS.value,
                    "reason": "not_esp",
                },
            )
            return IPSecPolicyAction.BYPASS, packet.clone()

        if len(packet.headers) < 2 or not isinstance(packet.headers[1], ESPHeader):
            self.emit_trace(
                layer=Layer.CRYPTO,
                event_type=EventType.FRAME_DROP,
                packet_id=packet_id,
                details={"drop_reason": "missing_esp_header"},
            )
            return IPSecPolicyAction.DROP, None

        esp = packet.headers[1]
        sa = self.sad.get(esp.spi)
        if sa is None:
            self.emit_trace(
                layer=Layer.CRYPTO,
                event_type=EventType.IPSEC_SA_LOOKUP,
                packet_id=packet_id,
                details={
                    "direction": "inbound",
                    "spi": esp.spi,
                    "result": "miss",
                },
            )
            self.emit_trace(
                layer=Layer.CRYPTO,
                event_type=EventType.FRAME_DROP,
                packet_id=packet_id,
                details={"drop_reason": "unknown_spi", "spi": esp.spi},
            )
            return IPSecPolicyAction.DROP, None
        self.emit_trace(
            layer=Layer.CRYPTO,
            event_type=EventType.IPSEC_SA_LOOKUP,
            packet_id=packet_id,
            details={
                "direction": "inbound",
                "spi": esp.spi,
                "result": "hit",
            },
        )

        decapped = packet.clone()
        decapped.headers = decapped.headers[2:]
        self.emit_trace(
            layer=Layer.CRYPTO,
            event_type=EventType.IPSEC_POLICY_EVALUATE,
            packet_id=packet_id,
            details={
                "direction": "inbound",
                "action": IPSecPolicyAction.PROTECT.value,
                "reason": "sa_validated",
                "spi": esp.spi,
            },
        )
        self.emit_trace(
            layer=Layer.CRYPTO,
            event_type=EventType.CRYPTO_DECRYPT,
            packet_id=packet_id,
            details={
                "transform": "esp",
                "mode": IPSecMode.TUNNEL.value,
                "spi": esp.spi,
            },
        )
        self.emit_trace(
            layer=Layer.TUNNEL,
            event_type=EventType.ENCAP_POP,
            packet_id=packet_id,
            details={
                "outer_proto": "IPv4Header",
                "inner_proto": type(decapped.headers[0]).__name__ if decapped.headers else "payload",
                "tunnel_type": "ipsec",
            },
        )
        return IPSecPolicyAction.PROTECT, decapped

    def _match_policy(self, src_ip: str, dst_ip: str) -> SecurityPolicy | None:
        src = ip_address(src_ip)
        dst = ip_address(dst_ip)
        for policy in self.spd:
            if src in ip_network(policy.src_prefix, strict=False) and dst in ip_network(
                policy.dst_prefix,
                strict=False,
            ):
                return policy
        return None
