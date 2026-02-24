"""Edge-case tests for Lab 25 PMTUD and MSS behavior."""

from __future__ import annotations

import pytest

from pycie.model.headers import TCPHeader
from pycie.model.packet import PacketStack
from pycie.protocols.pmtud_mss import PMTUDMSSProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab25]


def test_evaluate_forward_without_ipv4_header_returns_reason() -> None:
    proc = PMTUDMSSProcess()
    forwarded, reason, mtu = proc.evaluate_forward(PacketStack(headers=[]), egress_mtu=900, now_ms=100)

    assert forwarded is None
    assert reason == "no_ipv4_header"
    assert mtu is None


def test_clamp_syn_mss_ignores_non_syn_packets() -> None:
    proc = PMTUDMSSProcess()
    packet = PacketStack(headers=[TCPHeader(src_port=1, dst_port=2, flags=frozenset({"ACK"}), mss=1300)], payload=b"")

    updated = proc.clamp_syn_mss(packet, now_ms=100)
    tcp = updated.headers[0]
    assert isinstance(tcp, TCPHeader)
    assert tcp.mss == 1300


def test_age_path_mtu_cache_expires_entries() -> None:
    proc = PMTUDMSSProcess(pmtu_timeout_ms=10)
    proc.learn_path_mtu(src_ip="10.0.0.1", dst_ip="10.0.0.2", mtu=1200, now_ms=0)

    proc.age_path_mtu_cache(now_ms=11)
    assert proc.effective_path_mtu(src_ip="10.0.0.1", dst_ip="10.0.0.2") == proc.default_path_mtu
