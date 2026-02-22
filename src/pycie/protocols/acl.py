"""Lab 31: ACL filtering model."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from ipaddress import ip_address, ip_network


class ACLAction(StrEnum):
    PERMIT = "permit"
    DENY = "deny"


@dataclass(frozen=True)
class ACLPacket:
    src_ip: str
    dst_ip: str
    protocol: str = "ip"
    src_port: int | None = None
    dst_port: int | None = None


@dataclass(frozen=True)
class ACLRule:
    seq: int
    action: "ACLAction | str"
    src_prefix: str = "0.0.0.0/0"
    dst_prefix: str = "0.0.0.0/0"
    protocol: str = "ip"
    src_port: int | None = None
    dst_port: int | None = None

    def matches(self, packet: ACLPacket) -> bool:
        packet_protocol = packet.protocol.lower()
        rule_protocol = self.protocol.lower()
        if rule_protocol != "ip" and rule_protocol != packet_protocol:
            return False

        if ip_address(packet.src_ip) not in ip_network(self.src_prefix, strict=False):
            return False
        if ip_address(packet.dst_ip) not in ip_network(self.dst_prefix, strict=False):
            return False

        if self.src_port is not None and packet.src_port != self.src_port:
            return False
        if self.dst_port is not None and packet.dst_port != self.dst_port:
            return False
        return True


@dataclass
class ACL:
    """Ordered ACL with first-match semantics and implicit deny."""

    rules: list[ACLRule] = field(default_factory=list)

    def add_rule(self, rule: ACLRule) -> None:
        """Insert or replace a rule by sequence number."""
        self.remove_rule(rule.seq)
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.seq)

    def remove_rule(self, seq: int) -> None:
        """Delete rule by sequence."""
        self.rules = [rule for rule in self.rules if rule.seq != seq]

    def evaluate(self, packet: ACLPacket) -> ACLAction:
        """Return ACL decision with implicit deny when no rule matches."""
        for rule in self.rules:
            if rule.matches(packet):
                return ACLAction(rule.action)
        return ACLAction.DENY
