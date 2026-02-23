"""Edge-case tests for Lab 20 IPv6 ND forwarding."""

from __future__ import annotations

import pytest

from pycie.model.headers import IPv4Header, IPv6Header
from pycie.model.packet import PacketStack
from pycie.protocols.ipv6_nd_forwarding import (
    IPv6NDForwarder,
    IPv6Route,
    NDNeighborAdvertisement,
)

pytestmark = [pytest.mark.exercise, pytest.mark.lab20]


def test_forward_without_ipv6_header_returns_reason() -> None:
    fwd = IPv6NDForwarder()
    pkt = PacketStack(headers=[IPv4Header(src_ip="1.1.1.1", dst_ip="2.2.2.2", ttl=64, protocol=6)])

    egress, out, reason = fwd.forward(pkt, now_ms=1000)
    assert (egress, out, reason) == (None, None, "no_ipv6_header")


def test_forward_hop_limit_expired_returns_reason() -> None:
    fwd = IPv6NDForwarder()
    fwd.install_route(IPv6Route(prefix="2001:db8::/32", next_hop="2001:db8::1", outgoing_interface="eth0"))
    fwd.learn_neighbor("2001:db8::1", "00:11:22:33:44:55", now_ms=1000)
    pkt = PacketStack(headers=[IPv6Header(src_ip="2001:db8:1::1", dst_ip="2001:db8:2::1", hop_limit=1)])

    egress, out, reason = fwd.forward(pkt, now_ms=1001)
    assert (egress, out, reason) == (None, None, "hop_limit_expired")


def test_forward_without_route_returns_reason() -> None:
    fwd = IPv6NDForwarder()
    pkt = PacketStack(headers=[IPv6Header(src_ip="2001:db8:1::1", dst_ip="2001:db8:999::1", hop_limit=64)])

    egress, out, reason = fwd.forward(pkt, now_ms=1001)
    assert (egress, out, reason) == (None, None, "no_route")


def test_age_neighbors_expires_entries() -> None:
    fwd = IPv6NDForwarder()
    fwd.learn_neighbor("2001:db8::1", "00:11:22:33:44:55", now_ms=0, ttl_ms=100)
    fwd.age_neighbors(now_ms=100)

    assert "2001:db8::1" not in fwd.neighbors
    assert fwd.should_solicit("2001:db8::1")


def test_resolve_neighbor_drops_pending_packet_with_expired_hop_limit() -> None:
    fwd = IPv6NDForwarder()
    fwd.install_route(IPv6Route(prefix="2001:db8:5::/64", next_hop="2001:db8::5", outgoing_interface="eth5"))
    pkt = PacketStack(headers=[IPv6Header(src_ip="2001:db8:1::1", dst_ip="2001:db8:5::20", hop_limit=1)])
    fwd.queue_pending("2001:db8::5", pkt, now_ms=2000)

    drained = fwd.resolve_neighbor(
        NDNeighborAdvertisement(target_ip="2001:db8::5", target_mac="11:22:33:44:55:66"),
        now_ms=2001,
    )
    assert drained == []
