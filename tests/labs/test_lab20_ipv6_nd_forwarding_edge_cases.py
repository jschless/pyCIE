"""Edge-case tests for Lab 20 IPv6 ND forwarding."""

from __future__ import annotations

import pytest

from pycie.model.headers import IPv6Header
from pycie.model.packet import PacketStack
from pycie.protocols.ipv6_nd_forwarding import IPv6NDForwarder, IPv6Route

pytestmark = [pytest.mark.exercise, pytest.mark.lab20]


def _pkt(dst: str, *, hop: int = 64) -> PacketStack:
    return PacketStack(headers=[IPv6Header(src_ip="2001:db8:1::1", dst_ip=dst, hop_limit=hop)], metadata={})


def test_forward_without_ipv6_header_returns_drop_reason() -> None:
    fwd = IPv6NDForwarder()
    egress, forwarded, reason = fwd.forward(PacketStack(headers=[]), now_ms=1000)

    assert (egress, forwarded, reason) == (None, None, "no_ipv6_header")


def test_forward_hop_limit_expired_drops_before_route_lookup() -> None:
    fwd = IPv6NDForwarder()
    fwd.install_route(IPv6Route(prefix="2001:db8:2::/64", next_hop=None, outgoing_interface="eth0"))

    egress, forwarded, reason = fwd.forward(_pkt("2001:db8:2::2", hop=1), now_ms=1000)
    assert (egress, forwarded, reason) == (None, None, "hop_limit_expired")


def test_forward_no_route_returns_no_route() -> None:
    fwd = IPv6NDForwarder()
    egress, forwarded, reason = fwd.forward(_pkt("2001:db8:9::1"), now_ms=1000)

    assert (egress, forwarded, reason) == (None, None, "no_route")


def test_age_neighbors_expires_old_entries() -> None:
    fwd = IPv6NDForwarder()
    fwd.learn_neighbor("2001:db8::9", "00:11:22:33:44:55", now_ms=0, ttl_ms=10)

    fwd.age_neighbors(now_ms=11)
    assert "2001:db8::9" not in fwd.neighbors
