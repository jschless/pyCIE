"""Exercise tests for Lab 12 IPsec."""

from __future__ import annotations

import pytest

from pycie.model.headers import IPv4Header
from pycie.model.packet import PacketStack
from pycie.protocols.ipsec import IPsecProcess, SecurityAssociation, SecurityPolicy

pytestmark = [pytest.mark.exercise, pytest.mark.lab12]


def test_outbound_protects_when_policy_requires() -> None:
    proc = IPsecProcess()
    proc.install_sa(SecurityAssociation(spi=101, src_ip="192.0.2.1", dst_ip="192.0.2.2"))
    proc.install_policy(SecurityPolicy("p1", "10.0.0.0/24", "10.1.0.0/24", action="protect", sa_spi=101))

    pkt = PacketStack(headers=[IPv4Header(src_ip="10.0.0.1", dst_ip="10.1.0.1", protocol=6)])
    action, out = proc.outbound(pkt)

    assert action == "protect"
    assert out is not None


def test_inbound_drop_when_spi_unknown() -> None:
    proc = IPsecProcess()
    pkt = PacketStack(headers=[IPv4Header(src_ip="192.0.2.2", dst_ip="192.0.2.1", protocol=50)])

    action, out = proc.inbound(pkt)
    assert action == "drop"
    assert out is None
