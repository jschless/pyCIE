"""Exercise tests for Lab 21 NAT44 pipeline."""

from __future__ import annotations

import pytest

from pycie.model.headers import IPv4Header
from pycie.model.packet import PacketStack
from pycie.protocols.nat44_pipeline import NAT44Pipeline, NAT44StaticRule

pytestmark = [pytest.mark.exercise, pytest.mark.lab21]


def _flow(src_ip: str, dst_ip: str, src_port: int, dst_port: int, proto: str = "tcp") -> PacketStack:
    return PacketStack(
        headers=[IPv4Header(src_ip=src_ip, dst_ip=dst_ip, ttl=64, protocol=6 if proto == "tcp" else 17)],
        metadata={"l4_proto": proto, "src_port": src_port, "dst_port": dst_port},
    )


def test_outbound_creates_dynamic_session_and_translates_source() -> None:
    nat = NAT44Pipeline(public_ip="198.51.100.10", port_min=20000, port_max=20010)
    pkt = _flow("10.1.1.10", "203.0.113.50", 12345, 443, "tcp")

    translated, reason = nat.translate_outbound(pkt, now_ms=1000)
    assert reason is None
    assert translated is not None
    ipv4 = translated.headers[0]
    assert isinstance(ipv4, IPv4Header)
    assert ipv4.src_ip == "198.51.100.10"
    assert translated.metadata["src_port"] == 20000
    assert len(nat.sessions) == 1


def test_outbound_reuses_existing_session_for_same_flow() -> None:
    nat = NAT44Pipeline(public_ip="198.51.100.10", port_min=20000, port_max=20010)
    pkt = _flow("10.1.1.10", "203.0.113.50", 12345, 443, "tcp")

    first, _ = nat.translate_outbound(pkt, now_ms=1000)
    second, _ = nat.translate_outbound(pkt, now_ms=2000)
    assert first is not None and second is not None
    assert first.metadata["src_port"] == second.metadata["src_port"]
    assert len(nat.sessions) == 1


def test_inbound_dynamic_flow_translates_back_to_inside_host() -> None:
    nat = NAT44Pipeline(public_ip="198.51.100.10", port_min=20000, port_max=20010)
    outbound = _flow("10.1.1.10", "203.0.113.50", 12345, 443, "tcp")
    translated, _ = nat.translate_outbound(outbound, now_ms=1000)
    assert translated is not None
    translated_port = translated.metadata["src_port"]

    inbound = _flow("203.0.113.50", "198.51.100.10", 443, translated_port, "tcp")
    restored, reason = nat.translate_inbound(inbound, now_ms=1500)
    assert reason is None
    assert restored is not None
    ipv4 = restored.headers[0]
    assert isinstance(ipv4, IPv4Header)
    assert ipv4.dst_ip == "10.1.1.10"
    assert restored.metadata["dst_port"] == 12345


def test_inbound_static_dnat_rule_is_applied_before_dynamic_lookup() -> None:
    nat = NAT44Pipeline(public_ip="198.51.100.10", port_min=20000, port_max=20010)
    nat.install_static_rule(
        NAT44StaticRule(
            public_ip="198.51.100.10",
            public_port=8443,
            inside_ip="10.99.0.10",
            inside_port=443,
            protocol="tcp",
        )
    )

    inbound = _flow("203.0.113.80", "198.51.100.10", 55555, 8443, "tcp")
    restored, reason = nat.translate_inbound(inbound, now_ms=1000)
    assert reason is None
    assert restored is not None
    ipv4 = restored.headers[0]
    assert isinstance(ipv4, IPv4Header)
    assert ipv4.dst_ip == "10.99.0.10"
    assert restored.metadata["dst_port"] == 443


def test_age_sessions_expires_idle_entries() -> None:
    nat = NAT44Pipeline(public_ip="198.51.100.10", port_min=20000, port_max=20010, session_timeout_ms=100)
    pkt = _flow("10.1.1.10", "203.0.113.50", 12345, 443, "tcp")
    nat.translate_outbound(pkt, now_ms=0)
    nat.age_sessions(now_ms=100)

    assert nat.sessions == {}
