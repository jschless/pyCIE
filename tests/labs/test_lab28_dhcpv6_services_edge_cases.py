"""Edge-case tests for Lab 28 DHCPv6 services."""

from __future__ import annotations

import pytest

from pycie.protocols.dhcpv6 import DHCPv6Server

pytestmark = [pytest.mark.exercise, pytest.mark.lab28]


def test_pool_exhaustion_returns_none_offer() -> None:
    server = DHCPv6Server(pool_cidr="2001:db8:200::/127")
    m1 = server.handle_solicit("duid-1", now_ms=0)
    assert m1 is not None
    server.handle_request("duid-1", m1.offered_ip, now_ms=1)

    m2 = server.handle_solicit("duid-2", now_ms=2)
    assert m2 is None


def test_request_for_out_of_pool_address_returns_noaddravail() -> None:
    server = DHCPv6Server(pool_cidr="2001:db8:200::/126")
    reply = server.handle_request("duid-1", "2001:db8:300::1", now_ms=0)

    assert reply.status == "noaddravail"


def test_age_leases_expires_entries() -> None:
    server = DHCPv6Server(pool_cidr="2001:db8:200::/126", lease_time_ms=10)
    offer = server.handle_solicit("duid-1", now_ms=0)
    assert offer is not None
    server.handle_request("duid-1", offer.offered_ip, now_ms=1)

    server.age_leases(now_ms=12)
    assert "duid-1" not in server.leases


def test_release_removes_lease() -> None:
    server = DHCPv6Server(pool_cidr="2001:db8:200::/126")
    offer = server.handle_solicit("duid-1", now_ms=0)
    assert offer is not None
    server.handle_request("duid-1", offer.offered_ip, now_ms=1)

    server.release("duid-1")
    assert "duid-1" not in server.leases
