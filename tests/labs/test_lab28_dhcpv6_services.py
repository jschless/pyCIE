"""Exercise tests for Lab 28 DHCPv6 services."""

from __future__ import annotations

import pytest

from pycie.protocols.dhcpv6 import DHCPv6MessageType, DHCPv6Server

pytestmark = [pytest.mark.exercise, pytest.mark.lab28]


def test_handle_solicit_returns_advertise_with_offer() -> None:
    server = DHCPv6Server(pool_cidr="2001:db8:200::/126")
    message = server.handle_solicit("duid-1", now_ms=0)

    assert message is not None
    assert message.msg_type == DHCPv6MessageType.ADVERTISE
    assert message.offered_ip is not None


def test_handle_request_commits_lease_and_replies() -> None:
    server = DHCPv6Server(pool_cidr="2001:db8:200::/126")
    offer = server.handle_solicit("duid-1", now_ms=0)
    assert offer is not None

    reply = server.handle_request("duid-1", offer.offered_ip, now_ms=1)
    assert reply.msg_type == DHCPv6MessageType.REPLY
    assert reply.status == "success"
    assert "duid-1" in server.leases


def test_renew_extends_existing_lease() -> None:
    server = DHCPv6Server(pool_cidr="2001:db8:200::/126", lease_time_ms=100)
    offer = server.handle_solicit("duid-1", now_ms=0)
    assert offer is not None
    server.handle_request("duid-1", offer.offered_ip, now_ms=1)

    renewed = server.renew("duid-1", now_ms=50)
    assert renewed is not None
    assert server.leases["duid-1"].expires_at_ms == 150


def test_relay_stamps_link_address() -> None:
    server = DHCPv6Server()
    offer = server.handle_solicit("duid-1", now_ms=0)
    assert offer is not None

    relayed = server.relay(offer, "2001:db8:ffff::1")
    assert relayed.relay_link_address == "2001:db8:ffff::1"
