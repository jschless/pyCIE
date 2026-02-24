"""Lab 25: path MTU discovery and TCP MSS clamp helpers."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from pycie.model.headers import IPv4Header, TCPHeader
from pycie.model.packet import PacketStack

from .base import ProtocolBase

IPV4_HEADER_BYTES = 20
TCP_HEADER_BYTES = 20


@dataclass(frozen=True)
class PMTUEntry:
    mtu: int
    learned_at_ms: int


@dataclass
class PMTUDMSSProcess(ProtocolBase):
    """Maintain PMTU cache and clamp SYN MSS for constrained paths."""

    name: str = "pmtud_mss"
    default_path_mtu: int = 1_500
    min_ipv4_mtu: int = 68
    pmtu_timeout_ms: int = 600_000
    pmtu_cache: dict[tuple[str, str], PMTUEntry] = field(default_factory=dict)

    def evaluate_forward(
        self,
        packet: PacketStack,
        *,
        egress_mtu: int,
        now_ms: int,
        path_key: tuple[str, str] | None = None,
        tunnel_overhead_bytes: int = 0,
    ) -> tuple[PacketStack | None, str | None, int | None]:
        """Return forward decision and PMTU signal metadata for one packet."""
        ipv4 = _find_ipv4(packet)
        if ipv4 is None:
            return None, "no_ipv4_header", None

        effective_mtu = max(self.min_ipv4_mtu, egress_mtu - tunnel_overhead_bytes)
        packet_size = IPV4_HEADER_BYTES + len(packet.payload)
        key = path_key or (ipv4.src_ip, ipv4.dst_ip)

        if "DF" in ipv4.flags and packet_size > effective_mtu:
            self.learn_path_mtu(src_ip=key[0], dst_ip=key[1], mtu=effective_mtu, now_ms=now_ms)
            return None, "fragmentation_needed", effective_mtu

        return packet.clone(), None, None

    def learn_path_mtu(self, *, src_ip: str, dst_ip: str, mtu: int, now_ms: int) -> None:
        """Update PMTU cache with lower bound validation."""
        bounded = max(self.min_ipv4_mtu, mtu)
        key = (src_ip, dst_ip)
        previous = self.pmtu_cache.get(key)
        if previous is None or bounded <= previous.mtu:
            self.pmtu_cache[key] = PMTUEntry(mtu=bounded, learned_at_ms=now_ms)
            return
        self.pmtu_cache[key] = PMTUEntry(mtu=bounded, learned_at_ms=now_ms)

    def effective_path_mtu(self, *, src_ip: str, dst_ip: str) -> int:
        """Return cached PMTU when present, otherwise default path MTU."""
        entry = self.pmtu_cache.get((src_ip, dst_ip))
        if entry is None:
            return self.default_path_mtu
        return entry.mtu

    def clamp_syn_mss(
        self,
        packet: PacketStack,
        *,
        now_ms: int,
        tunnel_overhead_bytes: int = 0,
        min_mss: int = 536,
    ) -> PacketStack:
        """Clamp MSS in TCP SYN packet based on learned PMTU."""
        del now_ms
        updated = packet.clone()
        ipv4 = _find_ipv4(updated)
        if ipv4 is None:
            return updated

        for index, header in enumerate(updated.headers):
            if not isinstance(header, TCPHeader):
                continue
            if "SYN" not in header.flags or header.mss is None:
                return updated

            pmtu = self.effective_path_mtu(src_ip=ipv4.src_ip, dst_ip=ipv4.dst_ip)
            effective_mtu = max(self.min_ipv4_mtu, pmtu - tunnel_overhead_bytes)
            max_mss = max(min_mss, effective_mtu - IPV4_HEADER_BYTES - TCP_HEADER_BYTES)
            new_mss = min(header.mss, max_mss)
            updated.headers[index] = replace(header, mss=new_mss)
            if new_mss != header.mss:
                updated.metadata["mss_clamped_to"] = new_mss
            return updated
        return updated

    def age_path_mtu_cache(self, *, now_ms: int) -> None:
        """Expire stale PMTU cache entries."""
        expired = [
            key
            for key, entry in self.pmtu_cache.items()
            if now_ms - entry.learned_at_ms >= self.pmtu_timeout_ms
        ]
        for key in expired:
            del self.pmtu_cache[key]


def _find_ipv4(packet: PacketStack) -> IPv4Header | None:
    return next((header for header in packet.headers if isinstance(header, IPv4Header)), None)
