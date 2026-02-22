"""Exercise tests for Lab 33 DHCP services."""

from __future__ import annotations

import pytest

from pycie.protocols.dhcp import DHCPMessage, DHCPMessageType, DHCPServer

pytestmark = [pytest.mark.exercise, pytest.mark.lab33]


def test_discover_returns_lowest_available_offer() -> None:
    server = DHCPServer(pool_cidr="192.0.2.0/29")

    offer = server.handle_discover("client-a", now_ms=0)
    assert offer is not None
    assert offer.msg_type == DHCPMessageType.OFFER
    assert offer.yiaddr == "192.0.2.1"


def test_request_ack_installs_lease() -> None:
    server = DHCPServer(pool_cidr="192.0.2.0/29", lease_time_ms=1_000)
    server.handle_discover("client-a", now_ms=0)

    ack = server.handle_request("client-a", "192.0.2.1", now_ms=1)
    assert ack.msg_type == DHCPMessageType.ACK
    assert server.leases["client-a"].ip == "192.0.2.1"


def test_request_naks_when_ip_already_leased_to_other_client() -> None:
    server = DHCPServer(pool_cidr="192.0.2.0/29")
    server.handle_discover("client-a", now_ms=0)
    server.handle_request("client-a", "192.0.2.1", now_ms=1)

    nak = server.handle_request("client-b", "192.0.2.1", now_ms=2)
    assert nak.msg_type == DHCPMessageType.NAK


def test_renew_extends_existing_lease_expiration() -> None:
    server = DHCPServer(pool_cidr="192.0.2.0/29", lease_time_ms=1_000)
    server.handle_discover("client-a", now_ms=0)
    server.handle_request("client-a", "192.0.2.1", now_ms=10)
    first_expiry = server.leases["client-a"].expires_at_ms

    ack = server.renew("client-a", now_ms=900)
    assert ack is not None
    assert ack.msg_type == DHCPMessageType.ACK
    assert server.leases["client-a"].expires_at_ms > first_expiry


def test_age_leases_reclaims_expired_ip() -> None:
    server = DHCPServer(pool_cidr="192.0.2.0/29", lease_time_ms=100)
    server.handle_discover("client-a", now_ms=0)
    server.handle_request("client-a", "192.0.2.1", now_ms=1)

    server.age_leases(now_ms=200)
    assert "client-a" not in server.leases

    offer = server.handle_discover("client-b", now_ms=201)
    assert offer is not None
    assert offer.yiaddr == "192.0.2.1"


def test_pool_exhaustion_returns_none_offer() -> None:
    server = DHCPServer(pool_cidr="192.0.2.0/30")  # hosts: .1 and .2
    for idx, ip in enumerate(["192.0.2.1", "192.0.2.2"], start=1):
        cid = f"client-{idx}"
        server.handle_discover(cid, now_ms=idx)
        server.handle_request(cid, ip, now_ms=idx)

    assert server.handle_discover("client-3", now_ms=10) is None


def test_release_frees_lease_and_offer_state() -> None:
    server = DHCPServer(pool_cidr="192.0.2.0/29")
    server.handle_discover("client-a", now_ms=0)
    server.handle_request("client-a", "192.0.2.1", now_ms=1)

    server.release("client-a")
    assert "client-a" not in server.leases
    assert "client-a" not in server.offers


def test_relay_sets_gateway_ip() -> None:
    discover = DHCPMessage(msg_type=DHCPMessageType.DISCOVER, client_id="client-a")
    relayed = DHCPServer.relay(discover, relay_ip="198.51.100.1")

    assert relayed.giaddr == "198.51.100.1"
    assert relayed.client_id == "client-a"


def test_request_outside_pool_is_nak() -> None:
    server = DHCPServer(pool_cidr="192.0.2.0/29")
    response = server.handle_request("client-a", "203.0.113.10", now_ms=1)
    assert response.msg_type == DHCPMessageType.NAK
