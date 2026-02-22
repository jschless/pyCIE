"""Lab 34: multicast foundations (IGMP + simplified RPF/PIM behavior)."""

from __future__ import annotations

from dataclasses import dataclass, field
from ipaddress import ip_address, ip_network


@dataclass(frozen=True)
class MulticastForwardingEntry:
    source_ip: str
    group_ip: str
    rpf_if: str
    outgoing_ifs: tuple[str, ...]
    updated_at_ms: float


@dataclass
class MulticastProcess:
    """Simplified multicast control-plane state and forwarding decisions."""

    group_members: dict[str, set[str]] = field(default_factory=dict)
    rpf_routes: dict[str, str] = field(default_factory=dict)
    sg_state: dict[tuple[str, str], MulticastForwardingEntry] = field(default_factory=dict)

    def join_group(self, if_name: str, group_ip: str) -> None:
        """Record IGMP membership report on an interface."""
        self.group_members.setdefault(group_ip, set()).add(if_name)

    def leave_group(self, if_name: str, group_ip: str) -> None:
        """Remove IGMP membership report on an interface."""
        members = self.group_members.get(group_ip)
        if members is None:
            return
        members.discard(if_name)
        if not members:
            del self.group_members[group_ip]

    def install_rpf_route(self, source_prefix: str, ingress_if: str) -> None:
        """Install source-to-RPF interface mapping."""
        self.rpf_routes[source_prefix] = ingress_if

    def expected_rpf_interface(self, source_ip: str) -> str | None:
        """Resolve expected RPF interface with longest prefix match."""
        source = ip_address(source_ip)
        best: tuple[int, str] | None = None
        for prefix, if_name in self.rpf_routes.items():
            net = ip_network(prefix, strict=False)
            if source not in net:
                continue
            candidate = (net.prefixlen, if_name)
            if best is None or candidate[0] > best[0] or (
                candidate[0] == best[0] and candidate[1] < best[1]
            ):
                best = candidate
        return None if best is None else best[1]

    def rpf_check(self, source_ip: str, ingress_if: str) -> bool:
        """True when packet arrives on expected RPF interface."""
        expected = self.expected_rpf_interface(source_ip)
        if expected is None:
            return False
        return expected == ingress_if

    def compute_egress_interfaces(
        self,
        source_ip: str,
        group_ip: str,
        ingress_if: str,
    ) -> list[str]:
        """Compute outgoing interface list for an (S,G) flow."""
        if not self.rpf_check(source_ip, ingress_if):
            return []
        members = self.group_members.get(group_ip, set())
        return sorted(if_name for if_name in members if if_name != ingress_if)

    def process_data(
        self,
        source_ip: str,
        group_ip: str,
        ingress_if: str,
        *,
        now_ms: float,
    ) -> MulticastForwardingEntry | None:
        """Process source traffic and update forwarding state."""
        expected = self.expected_rpf_interface(source_ip)
        if expected is None or expected != ingress_if:
            return None

        outgoing = tuple(self.compute_egress_interfaces(source_ip, group_ip, ingress_if))
        entry = MulticastForwardingEntry(
            source_ip=source_ip,
            group_ip=group_ip,
            rpf_if=ingress_if,
            outgoing_ifs=outgoing,
            updated_at_ms=now_ms,
        )
        self.sg_state[(source_ip, group_ip)] = entry
        return entry
