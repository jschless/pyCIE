"""Edge-case tests for Lab 21 NAT44 pipeline."""

from __future__ import annotations

import pytest

from pycie.model.headers import IPv4Header
from pycie.model.packet import PacketStack
from pycie.protocols.nat44_pipeline import NAT44Pipeline

pytestmark = [pytest.mark.exercise, pytest.mark.lab21]


def _ipv4_packet(src_ip: str, dst_ip: str, *, proto: str = "tcp", src_port: int = 12000, dst_port: int = 443) -> PacketStack:
    return PacketStack(
        headers=[IPv4Header(src_ip=src_ip, dst_ip=dst_ip, protocol=6 if proto == "tcp" else 17)],
        metadata={"l4_proto": proto, "src_port": src_port, "dst_port": dst_port},
    )


def test_outbound_without_ipv4_header_fails() -> None:
    nat = NAT44Pipeline()
    translated, reason = nat.translate_outbound(PacketStack(headers=[], metadata={}), now_ms=1000)

    assert translated is None
    assert reason == "no_ipv4_header"


def test_outbound_missing_l4_tuple_fails() -> None:
    nat = NAT44Pipeline()
    packet = PacketStack(headers=[IPv4Header(src_ip="10.0.0.1", dst_ip="198.51.100.1", protocol=6)], metadata={})

    translated, reason = nat.translate_outbound(packet, now_ms=1000)
    assert translated is None
    assert reason == "missing_l4_tuple"


def test_outbound_pool_exhaustion_returns_error() -> None:
    nat = NAT44Pipeline(port_min=10000, port_max=10000)
    first, reason = nat.translate_outbound(_ipv4_packet("10.0.0.1", "198.51.100.1", src_port=1111), now_ms=1000)
    assert first is not None
    assert reason is None

    second, reason = nat.translate_outbound(_ipv4_packet("10.0.0.2", "198.51.100.2", src_port=2222), now_ms=1001)
    assert second is None
    assert reason == "nat_pool_exhausted"


def test_inbound_mismatched_return_path_is_rejected() -> None:
    nat = NAT44Pipeline(public_ip="203.0.113.10")
    outbound, _ = nat.translate_outbound(_ipv4_packet("10.1.1.10", "198.51.100.20", dst_port=80), now_ms=1000)
    assert outbound is not None

    wrong_src = _ipv4_packet(
        src_ip="198.51.100.99",
        dst_ip="203.0.113.10",
        src_port=80,
        dst_port=outbound.metadata["src_port"],
    )
    translated, reason = nat.translate_inbound(wrong_src, now_ms=1002)

    assert translated is None
    assert reason == "return_path_mismatch"
