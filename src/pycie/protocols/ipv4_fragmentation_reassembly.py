"""Lab 24: deterministic IPv4 fragmentation and reassembly model."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from pycie.model.headers import IPv4Header
from pycie.model.packet import PacketStack

from .base import ProtocolBase

IPV4_HEADER_BYTES = 20


@dataclass(frozen=True)
class FragmentFlowKey:
    src_ip: str
    dst_ip: str
    protocol: int
    identification: int


@dataclass
class FragmentBuffer:
    first_seen_ms: int
    fragments: list[PacketStack] = field(default_factory=list)


@dataclass
class IPv4FragmentationReassemblyProcess(ProtocolBase):
    """Fragment IPv4 packets by MTU and reassemble deterministically."""

    name: str = "ipv4_fragmentation_reassembly"
    reassembly_timeout_ms: int = 30_000
    buffers: dict[FragmentFlowKey, FragmentBuffer] = field(default_factory=dict)
    _next_identification: int = 1

    def fragment(self, packet: PacketStack, *, mtu: int) -> tuple[list[PacketStack], str | None]:
        """Split one IPv4 packet into fragments honoring DF behavior."""
        ipv4 = _ipv4_header(packet)
        if ipv4 is None:
            return [], "no_ipv4_header"
        if mtu <= IPV4_HEADER_BYTES:
            return [], "mtu_too_small"

        total_bytes = IPV4_HEADER_BYTES + len(packet.payload)
        if total_bytes <= mtu:
            updated = packet.clone()
            updated.headers = [replace(ipv4, total_length=total_bytes), *updated.headers[1:]]
            return [updated], None

        if "DF" in ipv4.flags:
            return [], "df_set_fragmentation_needed"

        chunk_size = ((mtu - IPV4_HEADER_BYTES) // 8) * 8
        if chunk_size <= 0:
            return [], "mtu_too_small"

        identification = ipv4.identification or self._allocate_identification()
        fragments: list[PacketStack] = []
        payload = packet.payload

        for offset in range(0, len(payload), chunk_size):
            chunk = payload[offset : offset + chunk_size]
            more_fragments = offset + chunk_size < len(payload)
            flags = frozenset({"MF"}) if more_fragments else frozenset()
            header = replace(
                ipv4,
                identification=identification,
                flags=flags,
                fragment_offset=offset // 8,
                total_length=IPV4_HEADER_BYTES + len(chunk),
            )
            fragments.append(PacketStack(headers=[header], payload=chunk, metadata=dict(packet.metadata)))

        return fragments, None

    def reassemble(self, fragments: list[PacketStack]) -> tuple[PacketStack | None, str | None]:
        """Reassemble fragments into one packet using first-fragment-wins overlap policy."""
        if not fragments:
            return None, "no_fragments"

        key = _fragment_key(fragments[0])
        if key is None:
            return None, "no_ipv4_header"

        for fragment in fragments[1:]:
            if _fragment_key(fragment) != key:
                return None, "invalid_fragment_set"

        ordered = sorted(fragments, key=lambda item: _ipv4_header(item).fragment_offset if _ipv4_header(item) else 0)

        assembled = bytearray()
        expected_offset_bytes = 0
        last_fragment_seen = False

        for fragment in ordered:
            header = _ipv4_header(fragment)
            if header is None:
                return None, "no_ipv4_header"

            offset_bytes = header.fragment_offset * 8
            if offset_bytes > expected_offset_bytes:
                return None, "missing_fragment_gap"

            skip = max(0, expected_offset_bytes - offset_bytes)
            new_bytes = fragment.payload[skip:]
            if new_bytes:
                assembled.extend(new_bytes)
                expected_offset_bytes += len(new_bytes)

            if "MF" not in header.flags:
                last_fragment_seen = True

        if not last_fragment_seen:
            return None, "incomplete_last_fragment"

        first_header = _ipv4_header(ordered[0])
        assert first_header is not None
        rebuilt_header = replace(
            first_header,
            flags=frozenset(),
            fragment_offset=0,
            total_length=IPV4_HEADER_BYTES + len(assembled),
        )
        return PacketStack(headers=[rebuilt_header], payload=bytes(assembled), metadata=dict(ordered[0].metadata)), None

    def ingest_fragment(
        self,
        fragment: PacketStack,
        *,
        now_ms: int,
    ) -> tuple[FragmentFlowKey | None, PacketStack | None, str | None]:
        """Ingest one fragment into buffer and return packet once complete."""
        self.age_reassembly_buffers(now_ms=now_ms)
        key = _fragment_key(fragment)
        if key is None:
            return None, None, "no_ipv4_header"

        buffer = self.buffers.setdefault(key, FragmentBuffer(first_seen_ms=now_ms))
        buffer.fragments.append(fragment.clone())
        packet, reason = self.reassemble(buffer.fragments)
        if packet is not None:
            del self.buffers[key]
            return key, packet, None

        if reason in {"invalid_fragment_set", "no_ipv4_header"}:
            return key, None, reason
        return key, None, None

    def age_reassembly_buffers(self, *, now_ms: int) -> None:
        """Expire old fragment buffers."""
        expired = [
            key
            for key, buffer in self.buffers.items()
            if now_ms - buffer.first_seen_ms >= self.reassembly_timeout_ms
        ]
        for key in expired:
            del self.buffers[key]

    def _allocate_identification(self) -> int:
        value = self._next_identification
        self._next_identification = (self._next_identification + 1) % 65_536
        if self._next_identification == 0:
            self._next_identification = 1
        return value


def _ipv4_header(packet: PacketStack) -> IPv4Header | None:
    return next((header for header in packet.headers if isinstance(header, IPv4Header)), None)


def _fragment_key(packet: PacketStack) -> FragmentFlowKey | None:
    ipv4 = _ipv4_header(packet)
    if ipv4 is None:
        return None
    return FragmentFlowKey(
        src_ip=ipv4.src_ip,
        dst_ip=ipv4.dst_ip,
        protocol=ipv4.protocol,
        identification=ipv4.identification,
    )
