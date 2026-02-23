"""Edge-case tests for Lab 07 IPv4 forwarding."""

from __future__ import annotations

import pytest

from pycie.forwarding.l3 import IPv4Forwarder, L3Route
from pycie.model.headers import Dot1QHeader, IPv4Header
from pycie.model.packet import PacketStack

pytestmark = [pytest.mark.exercise, pytest.mark.lab07]


def test_forward_without_ipv4_header_returns_reason() -> None:
    fwd = IPv4Forwarder()
    pkt = PacketStack(headers=[Dot1QHeader(vlan_id=10)], payload=b"x")

    egress, out, reason = fwd.forward(pkt)
    assert (egress, out, reason) == (None, None, "no_ipv4_header")


def test_forward_without_route_returns_no_route() -> None:
    fwd = IPv4Forwarder()
    pkt = PacketStack(headers=[IPv4Header(src_ip="10.0.0.1", dst_ip="203.0.113.5", ttl=64, protocol=17)])

    egress, out, reason = fwd.forward(pkt)
    assert (egress, out, reason) == (None, None, "no_route")


def test_remove_route_only_affects_selected_route_type() -> None:
    fwd = IPv4Forwarder()
    static = L3Route("10.0.0.0/24", "192.0.2.1", "eth0", "static", 1, 10)
    ospf = L3Route("10.0.0.0/24", "192.0.2.2", "eth1", "ospf", 110, 20)
    fwd.install_route(static)
    fwd.install_route(ospf)

    fwd.remove_route("10.0.0.0/24", "ospf")

    assert static in fwd.routes
    assert ospf not in fwd.routes
