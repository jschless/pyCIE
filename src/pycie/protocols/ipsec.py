"""Lab 12: IPsec tunnel-mode scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field
from ipaddress import ip_address, ip_network

from pycie.model.headers import ESPHeader, IPv4Header
from pycie.model.packet import PacketStack

from .base import ProtocolBase


@dataclass(frozen=True)
class SecurityAssociation:
    spi: int
    src_ip: str
    dst_ip: str
    mode: str = "tunnel"
    encryption: str = "aes-gcm"
    auth: str = "sha256"


@dataclass(frozen=True)
class SecurityPolicy:
    policy_id: str
    src_prefix: str
    dst_prefix: str
    action: str  # protect | bypass | drop
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

    def outbound(self, packet: PacketStack) -> tuple[str, PacketStack | None]:
        """Return (action, packet_or_none) after SPD/SAD outbound processing."""
        ip_header = next((h for h in packet.headers if isinstance(h, IPv4Header)), None)
        if ip_header is None:
            return "drop", None

        policy = self._match_policy(ip_header.src_ip, ip_header.dst_ip)
        if policy is None:
            return "bypass", packet.clone()

        if policy.action == "drop":
            return "drop", None
        if policy.action == "bypass":
            return "bypass", packet.clone()

        if policy.sa_spi is None:
            return "drop", None
        sa = self.sad.get(policy.sa_spi)
        if sa is None:
            return "drop", None

        protected = packet.clone()
        protected.push_header(ESPHeader(spi=sa.spi, sequence=1, encrypted=True))
        protected.push_header(IPv4Header(src_ip=sa.src_ip, dst_ip=sa.dst_ip, protocol=50))
        return "protect", protected

    def inbound(self, packet: PacketStack) -> tuple[str, PacketStack | None]:
        """Return (action, packet_or_none) after inbound ESP processing."""
        if not packet.headers:
            return "drop", None

        outer = packet.headers[0]
        if not isinstance(outer, IPv4Header) or outer.protocol != 50:
            return "bypass", packet.clone()

        if len(packet.headers) < 2 or not isinstance(packet.headers[1], ESPHeader):
            return "drop", None

        esp = packet.headers[1]
        if esp.spi not in self.sad:
            return "drop", None

        decapped = packet.clone()
        decapped.headers = decapped.headers[2:]
        return "protect", decapped

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
