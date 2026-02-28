"""Edge-case tests for Lab 12 IPsec."""

from __future__ import annotations

import pytest

from pycie.model.headers import ESPHeader, IPv4Header
from pycie.model.packet import PacketStack
from pycie.protocols.ipsec import IPsecProcess, SecurityAssociation, SecurityPolicy

pytestmark = [pytest.mark.exercise, pytest.mark.lab12]


def test_outbound_without_matching_policy_bypasses() -> None:
    proc = IPsecProcess()
    pkt = PacketStack(headers=[IPv4Header(src_ip="10.0.0.1", dst_ip="10.9.0.1", protocol=6)])

    action, out = proc.outbound(pkt)
    assert action == "bypass"
    assert out is not None


def test_outbound_protect_without_sa_drops() -> None:
    proc = IPsecProcess()
    proc.install_policy(SecurityPolicy("p1", "10.0.0.0/24", "10.1.0.0/24", action="protect", sa_spi=999))
    pkt = PacketStack(headers=[IPv4Header(src_ip="10.0.0.1", dst_ip="10.1.0.1", protocol=6)])

    action, out = proc.outbound(pkt)
    assert action == "drop"
    assert out is None


def test_inbound_non_esp_packet_bypasses() -> None:
    proc = IPsecProcess()
    pkt = PacketStack(headers=[IPv4Header(src_ip="192.0.2.2", dst_ip="192.0.2.1", protocol=6)])

    action, out = proc.inbound(pkt)
    assert action == "bypass"
    assert out is not None


def test_inbound_drops_when_sa_spi_matches_but_outer_endpoints_do_not() -> None:
    proc = IPsecProcess()
    proc.install_sa(SecurityAssociation(spi=101, src_ip="192.0.2.1", dst_ip="192.0.2.2"))
    pkt = PacketStack(
        headers=[
            IPv4Header(src_ip="192.0.2.99", dst_ip="192.0.2.2", protocol=50),
            ESPHeader(spi=101, sequence=1, encrypted=True),
            IPv4Header(src_ip="10.0.0.1", dst_ip="10.1.0.1", protocol=6),
        ]
    )

    action, out = proc.inbound(pkt)
    assert action == "drop"
    assert out is None


def test_inbound_accepts_when_spi_and_outer_endpoints_match_sa() -> None:
    proc = IPsecProcess()
    proc.install_sa(SecurityAssociation(spi=101, src_ip="192.0.2.1", dst_ip="192.0.2.2"))
    pkt = PacketStack(
        headers=[
            IPv4Header(src_ip="192.0.2.1", dst_ip="192.0.2.2", protocol=50),
            ESPHeader(spi=101, sequence=1, encrypted=True),
            IPv4Header(src_ip="10.0.0.1", dst_ip="10.1.0.1", protocol=6),
        ]
    )

    action, out = proc.inbound(pkt)
    assert action == "protect"
    assert out is not None
    assert len(out.headers) == 1
    assert isinstance(out.headers[0], IPv4Header)
