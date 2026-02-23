"""Edge-case tests for Lab 17 BGP FSM transport."""

from __future__ import annotations

import pytest

from pycie.protocols.bgp_fsm_transport import (
    BGPFSMState,
    BGPTransportNotification,
    BGPTransportOpen,
    BGPTransportSession,
    BGPTransportUpdate,
)

pytestmark = [pytest.mark.exercise, pytest.mark.lab17]


def _session() -> BGPTransportSession:
    return BGPTransportSession(
        peer_id="peer1",
        peer_as=65002,
        local_as=65001,
        local_router_id="1.1.1.1",
        configured_hold_time_s=30,
    )


def test_open_with_unacceptable_hold_time_resets_session() -> None:
    session = _session()
    session.start()
    session.on_tcp_up()

    response = session.receive_open(BGPTransportOpen(asn=65002, router_id="2.2.2.2", hold_time_s=2))
    assert isinstance(response, BGPTransportNotification)
    assert response.reason == "unacceptable_hold_time"
    assert session.state == BGPFSMState.IDLE


def test_update_before_established_triggers_notification() -> None:
    session = _session()
    session.start()
    session.on_tcp_up()

    response = session.receive_update(BGPTransportUpdate(prefix="198.51.100.0/24", next_hop="192.0.2.5"))
    assert isinstance(response, BGPTransportNotification)
    assert response.reason == "update_before_established"
    assert session.state == BGPFSMState.IDLE


def test_keepalive_in_idle_is_ignored() -> None:
    session = _session()
    assert not session.receive_keepalive()
    assert session.state == BGPFSMState.IDLE


def test_malformed_prefix_resets_established_session() -> None:
    session = _session()
    session.start()
    session.on_tcp_up()
    session.receive_open(BGPTransportOpen(asn=65002, router_id="2.2.2.2", hold_time_s=30))
    session.receive_keepalive()
    assert session.state == BGPFSMState.ESTABLISHED

    response = session.receive_update(BGPTransportUpdate(prefix="bad-prefix", next_hop="192.0.2.5"))
    assert isinstance(response, BGPTransportNotification)
    assert response.reason == "malformed_prefix"
    assert session.state == BGPFSMState.IDLE


def test_tcp_down_clears_state_and_rib() -> None:
    session = _session()
    session.start()
    session.on_tcp_up()
    session.receive_open(BGPTransportOpen(asn=65002, router_id="2.2.2.2", hold_time_s=30))
    session.receive_keepalive()
    session.receive_update(BGPTransportUpdate(prefix="203.0.113.0/24", next_hop="192.0.2.10"))

    session.on_tcp_down(reason="interface_down")
    assert session.state == BGPFSMState.IDLE
    assert session.last_error == "interface_down"
    assert session.adj_rib_in == {}
