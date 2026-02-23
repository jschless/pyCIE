"""Exercise tests for Lab 21 NAT44 pipeline."""

from __future__ import annotations

import pytest

from pycie.model.headers import IPv4Header
from pycie.model.packet import PacketStack
from pycie.protocols.nat44_pipeline import NAT44Pipeline, NAT44StaticRule

pytestmark = [pytest.mark.exercise, pytest.mark.lab21]


def _packet(src_ip: str, dst_ip: str, *, proto: str = "tcp", src_port: int = 12000, dst_port: int = 443) -> PacketStack:
    return PacketStack(
        headers=[IPv4Header(src_ip=src_ip, dst_ip=dst_ip, protocol=6 if proto == "tcp" else 17)],
        metadata={"l4_proto": proto, "src_port": src_port, "dst_port": dst_port},
    )


def test_outbound_translation_creates_session_and_rewrites_source_ip() -> None:
    nat = NAT44Pipeline(public_ip="203.0.113.10")

    translated, reason = nat.translate_outbound(_packet("10.1.1.10", "198.51.100.20"), now_ms=1000)
    assert reason is None
    assert translated is not None

    ipv4 = translated.headers[0]
    assert isinstance(ipv4, IPv4Header)
    assert ipv4.src_ip == "203.0.113.10"
    assert translated.metadata["nat_direction"] == "outbound"
    assert len(nat.sessions) == 1


def test_outbound_reuses_existing_translation_for_same_flow() -> None:
    nat = NAT44Pipeline(public_ip="203.0.113.10")

    first, _ = nat.translate_outbound(_packet("10.1.1.10", "198.51.100.20"), now_ms=1000)
    second, _ = nat.translate_outbound(_packet("10.1.1.10", "198.51.100.20"), now_ms=1010)

    assert first is not None and second is not None
    assert first.metadata["src_port"] == second.metadata["src_port"]


def test_inbound_dynamic_return_path_translates_back_to_inside_host() -> None:
    nat = NAT44Pipeline(public_ip="203.0.113.10")
    outbound, _ = nat.translate_outbound(_packet("10.1.1.10", "198.51.100.20", dst_port=80), now_ms=1000)
    assert outbound is not None

    inbound = _packet(
        src_ip="198.51.100.20",
        dst_ip="203.0.113.10",
        src_port=80,
        dst_port=outbound.metadata["src_port"],
    )
    translated, reason = nat.translate_inbound(inbound, now_ms=1005)

    assert reason is None
    assert translated is not None
    ipv4 = translated.headers[0]
    assert isinstance(ipv4, IPv4Header)
    assert ipv4.dst_ip == "10.1.1.10"
    assert translated.metadata["nat_direction"] == "inbound_dynamic"


def test_inbound_static_rule_translation() -> None:
    nat = NAT44Pipeline(public_ip="203.0.113.10")
    nat.install_static_rule(
        NAT44StaticRule(
            public_ip="203.0.113.10",
            public_port=443,
            inside_ip="10.1.1.20",
            inside_port=8443,
            protocol="tcp",
        )
    )

    translated, reason = nat.translate_inbound(
        _packet("198.51.100.30", "203.0.113.10", src_port=55000, dst_port=443),
        now_ms=2000,
    )

    assert reason is None
    assert translated is not None
    ipv4 = translated.headers[0]
    assert isinstance(ipv4, IPv4Header)
    assert ipv4.dst_ip == "10.1.1.20"
    assert translated.metadata["dst_port"] == 8443
    assert translated.metadata["nat_direction"] == "inbound_static"


def test_age_sessions_removes_expired_entries() -> None:
    nat = NAT44Pipeline(session_timeout_ms=100)
    nat.translate_outbound(_packet("10.1.1.10", "198.51.100.20"), now_ms=1000)

    nat.age_sessions(now_ms=1200)
    assert nat.sessions == {}
