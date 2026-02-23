"""Edge-case tests for Lab 33 DHCP services."""

from __future__ import annotations

import pytest

from pycie.protocols.dhcp import DHCPMessageType, DHCPServer

pytestmark = [pytest.mark.exercise, pytest.mark.lab33]


def test_request_without_requested_ip_uses_offer_state() -> None:
    server = DHCPServer(pool_cidr="192.0.2.0/29")
    offer = server.handle_discover("client-a", now_ms=1)
    assert offer is not None
    assert offer.yiaddr == "192.0.2.1"

    ack = server.handle_request("client-a", None, now_ms=2)
    assert ack.msg_type == DHCPMessageType.ACK
    assert ack.yiaddr == "192.0.2.1"


def test_renew_unknown_client_returns_none() -> None:
    server = DHCPServer(pool_cidr="192.0.2.0/29")
    assert server.renew("missing-client", now_ms=100) is None

