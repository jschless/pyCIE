"""Edge-case tests for Lab 24 IPv4 fragmentation and reassembly."""

from __future__ import annotations

import pytest

from pycie.model.headers import IPv4Header
from pycie.model.packet import PacketStack
from pycie.protocols.ipv4_fragmentation_reassembly import IPv4FragmentationReassemblyProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab24]


def test_fragment_without_ipv4_header_returns_reason() -> None:
    proc = IPv4FragmentationReassemblyProcess()
    fragments, reason = proc.fragment(PacketStack(headers=[]), mtu=1500)

    assert fragments == []
    assert reason == "no_ipv4_header"


def test_reassemble_detects_missing_fragment_gap() -> None:
    proc = IPv4FragmentationReassemblyProcess()
    f1 = PacketStack(
        headers=[IPv4Header(src_ip="10.0.0.1", dst_ip="10.0.0.2", protocol=17, identification=9, flags=frozenset({"MF"}), fragment_offset=0)],
        payload=b"abcdefgh",
    )
    f3 = PacketStack(
        headers=[IPv4Header(src_ip="10.0.0.1", dst_ip="10.0.0.2", protocol=17, identification=9, flags=frozenset(), fragment_offset=2)],
        payload=b"qrstuvwx",
    )

    rebuilt, reason = proc.reassemble([f1, f3])
    assert rebuilt is None
    assert reason == "missing_fragment_gap"


def test_age_reassembly_buffers_expires_old_entries() -> None:
    proc = IPv4FragmentationReassemblyProcess(reassembly_timeout_ms=10)
    fragment = PacketStack(
        headers=[IPv4Header(src_ip="10.0.0.1", dst_ip="10.0.0.2", protocol=17, identification=99, flags=frozenset({"MF"}), fragment_offset=0)],
        payload=b"abcdefgh",
    )

    key, packet, reason = proc.ingest_fragment(fragment, now_ms=100)
    assert key is not None
    assert packet is None
    assert reason is None

    proc.age_reassembly_buffers(now_ms=111)
    assert key not in proc.buffers
