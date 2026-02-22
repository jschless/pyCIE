"""Lab 08: ARP protocol scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from pycie.sim.network import Frame

from .base import ProtocolBase


class ARPOpcode(StrEnum):
    REQUEST = "request"
    REPLY = "reply"


@dataclass(frozen=True)
class ARPMessage:
    opcode: "ARPOpcode | str"
    sender_ip: str
    sender_mac: str
    target_ip: str
    target_mac: str | None = None


@dataclass
class ARPProcess(ProtocolBase):
    """Simplified ARP request/reply process.

    Reading:
    - RFC 826
    """

    name: str = "arp"
    ip_to_mac: dict[str, str] = field(default_factory=dict)
    local_ips: dict[str, str] = field(default_factory=dict)
    local_macs: dict[str, str] = field(default_factory=dict)
    outbound_messages: list[tuple[str, ARPMessage]] = field(default_factory=list)

    def on_frame(self, ingress_if: str, frame: Frame) -> None:
        """Parse inbound ARP payload from Ethernet frames."""
        if frame.ethertype != "0x0806":
            return
        if not isinstance(frame.payload, ARPMessage):
            return
        self.process_message(ingress_if, frame.payload)

    def build_request(self, sender_ip: str, sender_mac: str, target_ip: str) -> ARPMessage:
        """Construct an ARP request."""
        return ARPMessage(
            opcode=ARPOpcode.REQUEST,
            sender_ip=sender_ip,
            sender_mac=sender_mac,
            target_ip=target_ip,
            target_mac=None,
        )

    def build_reply(
        self,
        sender_ip: str,
        sender_mac: str,
        target_ip: str,
        target_mac: str,
    ) -> ARPMessage:
        """Construct an ARP reply."""
        return ARPMessage(
            opcode=ARPOpcode.REPLY,
            sender_ip=sender_ip,
            sender_mac=sender_mac,
            target_ip=target_ip,
            target_mac=target_mac,
        )

    def process_message(self, ingress_if: str, msg: ARPMessage) -> None:
        """Update ARP state and emit response actions when needed."""
        self.ip_to_mac[msg.sender_ip] = msg.sender_mac

        if ARPOpcode(msg.opcode) != ARPOpcode.REQUEST:
            return
        local_ip = self.local_ips.get(ingress_if)
        local_mac = self.local_macs.get(ingress_if)
        if local_ip is None or local_mac is None:
            return
        if msg.target_ip != local_ip:
            return

        reply = self.build_reply(
            sender_ip=local_ip,
            sender_mac=local_mac,
            target_ip=msg.sender_ip,
            target_mac=msg.sender_mac,
        )
        self.outbound_messages.append((ingress_if, reply))
