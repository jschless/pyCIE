"""Lab 26: IPv6 SLAAC with RA/RS and deterministic DAD handling."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import StrEnum
from ipaddress import IPv6Address, IPv6Network

from .base import ProtocolBase


class IPv6AddressState(StrEnum):
    TENTATIVE = "tentative"
    PREFERRED = "preferred"
    DUPLICATE = "duplicate"


@dataclass(frozen=True)
class RouterAdvertisement:
    prefix: str
    prefix_length: int = 64
    router_lifetime_s: int = 1800
    managed: bool = False
    other_config: bool = False


@dataclass(frozen=True)
class SLAACAddress:
    if_name: str
    address: str
    state: "IPv6AddressState | str"
    configured_at_ms: int


@dataclass
class IPv6SLAACProcess(ProtocolBase):
    """Generate SLAAC addresses and model RS/RA + DAD transitions."""

    name: str = "ipv6_slaac"
    router_advertisements: dict[str, RouterAdvertisement] = field(default_factory=dict)
    pending_rs: dict[str, int] = field(default_factory=dict)
    host_addresses: dict[str, SLAACAddress] = field(default_factory=dict)

    def configure_router(self, if_name: str, advertisement: RouterAdvertisement) -> None:
        """Install per-interface RA parameters."""
        self.router_advertisements[if_name] = advertisement

    def trigger_rs(self, if_name: str, *, now_ms: int, response_delay_ms: int = 10) -> None:
        """Schedule deterministic delayed RA emission for interface."""
        self.pending_rs[if_name] = now_ms + max(0, response_delay_ms)

    def emit_due_ra(self, *, now_ms: int) -> list[tuple[str, RouterAdvertisement]]:
        """Return RAs whose delay has elapsed."""
        emitted: list[tuple[str, RouterAdvertisement]] = []
        due_if_names = sorted(if_name for if_name, due_ms in self.pending_rs.items() if due_ms <= now_ms)
        for if_name in due_if_names:
            self.pending_rs.pop(if_name, None)
            advertisement = self.router_advertisements.get(if_name)
            if advertisement is not None:
                emitted.append((if_name, advertisement))
        return emitted

    def autoconfigure_from_ra(
        self,
        *,
        if_name: str,
        host_mac: str,
        now_ms: int,
    ) -> SLAACAddress:
        """Build tentative SLAAC address from configured RA prefix."""
        advertisement = self.router_advertisements.get(if_name)
        if advertisement is None:
            raise ValueError("missing_router_advertisement")

        address = build_slaac_address(advertisement.prefix, host_mac)
        state = SLAACAddress(
            if_name=if_name,
            address=address,
            state=IPv6AddressState.TENTATIVE,
            configured_at_ms=now_ms,
        )
        self.host_addresses[address] = state
        return state

    def complete_dad(self, address: str, *, conflict: bool, now_ms: int) -> SLAACAddress:
        """Finalize DAD state for one tentative address."""
        current = self.host_addresses.get(address)
        if current is None:
            raise ValueError("unknown_slaac_address")
        if IPv6AddressState(current.state) != IPv6AddressState.TENTATIVE:
            raise ValueError("dad_already_completed")

        new_state = IPv6AddressState.DUPLICATE if conflict else IPv6AddressState.PREFERRED
        updated = replace(current, state=new_state, configured_at_ms=now_ms)
        self.host_addresses[address] = updated
        return updated


def build_slaac_address(prefix: str, mac: str) -> str:
    """Derive deterministic /64 SLAAC address from prefix and host MAC."""
    network = IPv6Network(prefix, strict=False)
    if network.prefixlen > 64:
        raise ValueError("prefix_length_must_be_64_or_shorter")

    interface_id = derive_eui64_interface_id(mac)
    prefix_int = int(network.network_address) & ((1 << 128) - (1 << 64))
    return str(IPv6Address(prefix_int | interface_id))


def derive_eui64_interface_id(mac: str) -> int:
    """Build EUI-64 interface ID by inserting ff:fe and toggling U/L bit."""
    octets = mac.split(":")
    if len(octets) != 6:
        raise ValueError("invalid_mac")
    raw = [int(item, 16) for item in octets]
    raw[0] ^= 0x02  # flip universal/local bit
    eui64 = raw[:3] + [0xFF, 0xFE] + raw[3:]
    value = 0
    for octet in eui64:
        value = (value << 8) | octet
    return value
