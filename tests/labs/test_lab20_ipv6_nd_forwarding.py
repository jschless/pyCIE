"""Exercise tests for Lab 20 IPv6 ND forwarding."""

from __future__ import annotations

import pytest

from pycie.model.headers import IPv6Header
from pycie.model.packet import PacketStack
from pycie.protocols.ipv6_nd_forwarding import (
    IPv6NDForwarder,
    IPv6Route,
    NDNeighborAdvertisement,
)

pytestmark = [pytest.mark.exercise, pytest.mark.lab20]


def _packet(dst: str, hop: int = 64) -> PacketStack:
    return PacketStack(headers=[IPv6Header(src_ip="2001:db8:1::10", dst_ip=dst, hop_limit=hop)], metadata={})


def test_lookup_route_prefers_longest_prefix_then_metric() -> None:
    fwd = IPv6NDForwarder()
    fwd.install_route(IPv6Route(prefix="2001:db8::/32", next_hop="2001:db8::1", outgoing_interface="eth0", metric=20))
    fwd.install_route(prefix := IPv6Route(prefix="2001:db8:1::/48", next_hop="2001:db8:1::1", outgoing_interface="eth1", metric=10))

    best = fwd.lookup_route("2001:db8:1::abcd")
    assert best == prefix


def test_forward_resolves_known_neighbor_and_decrements_hop_limit() -> None:
    fwd = IPv6NDForwarder()
    fwd.install_route(IPv6Route(prefix="2001:db8:2::/64", next_hop="2001:db8::1", outgoing_interface="eth0"))
    fwd.learn_neighbor("2001:db8::1", "00:11:22:33:44:55", now_ms=1000)

    egress, forwarded, reason = fwd.forward(_packet("2001:db8:2::20"), now_ms=1001)
    assert reason is None
    assert egress == "eth0"
    assert forwarded is not None
    ipv6 = next(header for header in forwarded.headers if isinstance(header, IPv6Header))
    assert ipv6.hop_limit == 63
    assert forwarded.metadata["resolved_neighbor_mac"] == "00:11:22:33:44:55"


def test_forward_queues_when_neighbor_unresolved_and_resolve_drains_pending() -> None:
    fwd = IPv6NDForwarder()
    fwd.install_route(IPv6Route(prefix="2001:db8:3::/64", next_hop="2001:db8::9", outgoing_interface="eth9"))
    pkt = _packet("2001:db8:3::20")

    egress, forwarded, reason = fwd.forward(pkt, now_ms=2000)
    assert (egress, forwarded, reason) == (None, None, "neighbor_unresolved")
    assert len(fwd.pending["2001:db8::9"]) == 1
    assert fwd.should_solicit("2001:db8::9")

    drained = fwd.resolve_neighbor(
        NDNeighborAdvertisement(target_ip="2001:db8::9", target_mac="66:77:88:99:aa:bb"),
        now_ms=2001,
    )
    assert len(drained) == 1
    ipv6 = next(header for header in drained[0].headers if isinstance(header, IPv6Header))
    assert ipv6.hop_limit == 63
    assert "2001:db8::9" not in fwd.pending


def test_connected_route_uses_destination_as_next_hop() -> None:
    fwd = IPv6NDForwarder()
    fwd.install_route(IPv6Route(prefix="2001:db8:4::/64", next_hop=None, outgoing_interface="eth4"))
    fwd.learn_neighbor("2001:db8:4::20", "aa:bb:cc:dd:ee:ff", now_ms=100)

    egress, forwarded, reason = fwd.forward(_packet("2001:db8:4::20"), now_ms=101)
    assert reason is None
    assert egress == "eth4"
    assert forwarded is not None
