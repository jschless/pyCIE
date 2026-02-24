"""Exercise tests for Lab 24 IPv4 fragmentation and reassembly."""

from __future__ import annotations

import pytest

from pycie.model.headers import IPv4Header
from pycie.model.packet import PacketStack
from pycie.protocols.ipv4_fragmentation_reassembly import IPv4FragmentationReassemblyProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab24]


def _packet(*, df: bool = False, payload: bytes = b"abcdefghijklmnopqrst") -> PacketStack:
    flags = frozenset({"DF"}) if df else frozenset()
    return PacketStack(
        headers=[IPv4Header(src_ip="10.0.0.1", dst_ip="10.0.0.2", protocol=17, identification=7, flags=flags)],
        payload=payload,
    )


def test_fragment_splits_payload_by_mtu_into_ordered_offsets() -> None:
    proc = IPv4FragmentationReassemblyProcess()
    fragments, reason = proc.fragment(_packet(), mtu=28)

    assert reason is None
    assert len(fragments) == 3
    offsets = [fragment.headers[0].fragment_offset for fragment in fragments]
    assert offsets == [0, 1, 2]
    assert "MF" in fragments[0].headers[0].flags
    assert "MF" not in fragments[-1].headers[0].flags


def test_reassemble_restores_original_payload() -> None:
    proc = IPv4FragmentationReassemblyProcess()
    original = _packet(payload=b"0123456789abcdefghijkl")
    fragments, reason = proc.fragment(original, mtu=28)

    assert reason is None
    rebuilt, rebuild_reason = proc.reassemble(fragments)
    assert rebuild_reason is None
    assert rebuilt is not None
    assert rebuilt.payload == original.payload
    assert rebuilt.headers[0].fragment_offset == 0


def test_ingest_fragment_returns_packet_when_all_fragments_arrive() -> None:
    proc = IPv4FragmentationReassemblyProcess()
    fragments, reason = proc.fragment(_packet(payload=b"hello-fragmentation"), mtu=28)
    assert reason is None

    key = None
    packet = None
    for index, fragment in enumerate(fragments):
        key, packet, ingest_reason = proc.ingest_fragment(fragment, now_ms=1_000 + index)
        assert ingest_reason is None

    assert key is not None
    assert packet is not None
    assert packet.payload == b"hello-fragmentation"


def test_fragment_df_packet_returns_fragmentation_needed() -> None:
    proc = IPv4FragmentationReassemblyProcess()
    fragments, reason = proc.fragment(_packet(df=True), mtu=28)

    assert fragments == []
    assert reason == "df_set_fragmentation_needed"
