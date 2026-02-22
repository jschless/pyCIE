"""Exercise tests for Lab 07 IPv4 forwarding."""

from __future__ import annotations

import pytest

from pycie.forwarding.l3 import IPv4Forwarder, L3Route
from pycie.model.headers import IPv4Header
from pycie.model.packet import PacketStack

pytestmark = [pytest.mark.exercise, pytest.mark.lab07]


def test_lookup_prefers_longest_prefix() -> None:
    fwd = IPv4Forwarder()
    fwd.install_route(L3Route("10.0.0.0/8", "192.0.2.1", "eth0", "static", 1, 10))
    fwd.install_route(L3Route("10.1.0.0/16", "192.0.2.2", "eth1", "static", 1, 10))

    best = fwd.lookup("10.1.2.3")
    assert best is not None
    assert best.prefix == "10.1.0.0/16"


def test_lookup_tiebreaks_on_admin_distance_then_metric() -> None:
    fwd = IPv4Forwarder()
    fwd.install_route(L3Route("10.2.0.0/16", "192.0.2.1", "eth0", "ospf", 110, 20))
    fwd.install_route(L3Route("10.2.0.0/16", "192.0.2.2", "eth1", "bgp", 200, 5))

    best = fwd.lookup("10.2.1.1")
    assert best is not None
    assert best.next_hop == "192.0.2.1"


def test_forward_drops_ttl_expired_packet() -> None:
    fwd = IPv4Forwarder()
    fwd.install_route(L3Route("203.0.113.0/24", "192.0.2.1", "eth9", "static", 1, 1))
    pkt = PacketStack(headers=[IPv4Header(src_ip="1.1.1.1", dst_ip="203.0.113.7", ttl=1, protocol=17)])

    egress, out_packet, drop_reason = fwd.forward(pkt)
    assert egress is None
    assert out_packet is None
    assert drop_reason == "ttl_expired"
