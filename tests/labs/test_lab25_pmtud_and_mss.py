"""Exercise tests for Lab 25 PMTUD and MSS behavior."""

from __future__ import annotations

import pytest

from pycie.model.headers import IPv4Header, TCPHeader
from pycie.model.packet import PacketStack
from pycie.protocols.pmtud_mss import PMTUDMSSProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab25]


def _syn_packet(*, mss: int = 1460, df: bool = True, payload_len: int = 1200) -> PacketStack:
    flags = frozenset({"DF"}) if df else frozenset()
    return PacketStack(
        headers=[
            IPv4Header(src_ip="10.0.0.1", dst_ip="10.0.0.2", protocol=6, flags=flags),
            TCPHeader(src_port=12345, dst_port=443, flags=frozenset({"SYN"}), mss=mss),
        ],
        payload=b"x" * payload_len,
    )


def test_evaluate_forward_df_packet_returns_fragmentation_needed_and_caches_pmtu() -> None:
    proc = PMTUDMSSProcess()
    forwarded, reason, mtu = proc.evaluate_forward(_syn_packet(), egress_mtu=1000, now_ms=100)

    assert forwarded is None
    assert reason == "fragmentation_needed"
    assert mtu == 1000
    assert proc.effective_path_mtu(src_ip="10.0.0.1", dst_ip="10.0.0.2") == 1000


def test_effective_path_mtu_defaults_when_unknown() -> None:
    proc = PMTUDMSSProcess(default_path_mtu=1400)
    assert proc.effective_path_mtu(src_ip="192.0.2.1", dst_ip="198.51.100.1") == 1400


def test_clamp_syn_mss_uses_cached_pmtu() -> None:
    proc = PMTUDMSSProcess()
    proc.learn_path_mtu(src_ip="10.0.0.1", dst_ip="10.0.0.2", mtu=1200, now_ms=10)
    packet = proc.clamp_syn_mss(_syn_packet(mss=1460, payload_len=10), now_ms=20)

    tcp = packet.headers[1]
    assert isinstance(tcp, TCPHeader)
    assert tcp.mss == 1160
    assert packet.metadata["mss_clamped_to"] == 1160


def test_clamp_syn_mss_does_not_raise_existing_lower_mss() -> None:
    proc = PMTUDMSSProcess()
    proc.learn_path_mtu(src_ip="10.0.0.1", dst_ip="10.0.0.2", mtu=1200, now_ms=10)
    packet = proc.clamp_syn_mss(_syn_packet(mss=900, payload_len=10), now_ms=20)

    tcp = packet.headers[1]
    assert isinstance(tcp, TCPHeader)
    assert tcp.mss == 900
