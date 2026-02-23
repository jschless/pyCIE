"""Edge-case tests for Lab 21 NAT44 pipeline."""

from __future__ import annotations

import pytest

from pycie.model.headers import IPv4Header
from pycie.model.packet import PacketStack
from pycie.protocols.nat44_pipeline import NAT44Pipeline

pytestmark = [pytest.mark.exercise, pytest.mark.lab21]


def _flow(src_ip: str, dst_ip: str, src_port: int, dst_port: int, proto: str = "tcp") -> PacketStack:
    return PacketStack(
        headers=[IPv4Header(src_ip=src_ip, dst_ip=dst_ip, ttl=64, protocol=6 if proto == "tcp" else 17)],
        metadata={"l4_proto": proto, "src_port": src_port, "dst_port": dst_port},
    )


def test_outbound_without_l4_tuple_returns_error() -> None:
    nat = NAT44Pipeline()
    pkt = PacketStack(headers=[IPv4Header(src_ip="10.1.1.10", dst_ip="203.0.113.50", ttl=64, protocol=6)], metadata={})

    translated, reason = nat.translate_outbound(pkt, now_ms=1000)
    assert translated is None
    assert reason == "missing_l4_tuple"


def test_outbound_pool_exhaustion_returns_error() -> None:
    nat = NAT44Pipeline(public_ip="198.51.100.10", port_min=20000, port_max=20000)
    first = _flow("10.1.1.10", "203.0.113.50", 12345, 443, "tcp")
    second = _flow("10.1.1.11", "203.0.113.60", 12346, 443, "tcp")

    translated_first, reason_first = nat.translate_outbound(first, now_ms=1000)
    translated_second, reason_second = nat.translate_outbound(second, now_ms=1001)
    assert translated_first is not None and reason_first is None
    assert translated_second is None
    assert reason_second == "nat_pool_exhausted"


def test_inbound_without_session_returns_error() -> None:
    nat = NAT44Pipeline(public_ip="198.51.100.10")
    inbound = _flow("203.0.113.50", "198.51.100.10", 443, 29999, "tcp")

    translated, reason = nat.translate_inbound(inbound, now_ms=1000)
    assert translated is None
    assert reason == "session_not_found"


def test_inbound_return_path_mismatch_is_rejected() -> None:
    nat = NAT44Pipeline(public_ip="198.51.100.10", port_min=20000, port_max=20010)
    outbound = _flow("10.1.1.10", "203.0.113.50", 12345, 443, "tcp")
    translated_out, _ = nat.translate_outbound(outbound, now_ms=1000)
    assert translated_out is not None
    nat_port = translated_out.metadata["src_port"]

    inbound_wrong_peer = _flow("203.0.113.99", "198.51.100.10", 443, nat_port, "tcp")
    translated, reason = nat.translate_inbound(inbound_wrong_peer, now_ms=1500)
    assert translated is None
    assert reason == "return_path_mismatch"


def test_inbound_translated_ip_mismatch_is_rejected() -> None:
    nat = NAT44Pipeline(public_ip="198.51.100.10", port_min=20000, port_max=20010)
    outbound = _flow("10.1.1.10", "203.0.113.50", 12345, 443, "tcp")
    translated_out, _ = nat.translate_outbound(outbound, now_ms=1000)
    assert translated_out is not None
    nat_port = translated_out.metadata["src_port"]

    inbound_wrong_dst = _flow("203.0.113.50", "198.51.100.77", 443, nat_port, "tcp")
    translated, reason = nat.translate_inbound(inbound_wrong_dst, now_ms=1500)
    assert translated is None
    assert reason == "translated_ip_mismatch"
