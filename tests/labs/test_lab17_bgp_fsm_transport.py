"""Exercise tests for Lab 17 BGP FSM transport."""

from __future__ import annotations

import pytest

from pycie.protocols.bgp_fsm_transport import (
    BGPFSMState,
    BGPTransportKeepalive,
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


def _established_session() -> BGPTransportSession:
    session = _session()
    session.start()
    session.on_tcp_up()
    response = session.receive_open(BGPTransportOpen(asn=65002, router_id="2.2.2.2", hold_time_s=27))
    assert isinstance(response, BGPTransportKeepalive)
    assert session.receive_keepalive()
    assert session.state == BGPFSMState.ESTABLISHED
    return session


def test_valid_handshake_transitions_to_established() -> None:
    session = _session()
    session.start()

    open_out = session.on_tcp_up()
    assert open_out is not None
    assert open_out.asn == 65001
    assert session.state == BGPFSMState.OPENSENT

    keepalive = session.receive_open(BGPTransportOpen(asn=65002, router_id="2.2.2.2", hold_time_s=24))
    assert isinstance(keepalive, BGPTransportKeepalive)
    assert session.state == BGPFSMState.OPENCONFIRM
    assert session.negotiated_hold_time_s == 24
    assert session.keepalive_interval_s == 8

    assert session.receive_keepalive()
    assert session.state == BGPFSMState.ESTABLISHED


def test_established_session_installs_and_withdraws_updates() -> None:
    session = _established_session()

    assert session.receive_update(BGPTransportUpdate(prefix="203.0.113.0/24", next_hop="192.0.2.10")) is None
    assert "203.0.113.0/24" in session.adj_rib_in

    assert session.receive_update(
        BGPTransportUpdate(prefix="203.0.113.0/24", next_hop="192.0.2.10", withdraw=True)
    ) is None
    assert "203.0.113.0/24" not in session.adj_rib_in


def test_keepalive_timer_emits_periodic_keepalives() -> None:
    session = _established_session()
    # Negotiated hold-time is 27s so keepalive interval is 9s.
    keepalives = session.tick(20)

    assert len([item for item in keepalives if isinstance(item, BGPTransportKeepalive)]) == 2
    assert session.state == BGPFSMState.ESTABLISHED


def test_hold_timer_expiry_resets_session() -> None:
    session = _established_session()
    session.tick(27)

    assert session.state == BGPFSMState.IDLE
    assert session.last_error == "hold_timer_expired"
    assert session.adj_rib_in == {}


def test_receive_open_peer_as_mismatch_emits_notification_and_resets() -> None:
    session = _session()
    session.start()
    session.on_tcp_up()

    response = session.receive_open(BGPTransportOpen(asn=65111, router_id="2.2.2.2", hold_time_s=30))
    assert isinstance(response, BGPTransportNotification)
    assert response.reason == "peer_as_mismatch"
    assert session.state == BGPFSMState.IDLE
