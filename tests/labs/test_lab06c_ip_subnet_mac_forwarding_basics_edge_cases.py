"""Edge-case tests for Lab 06c IP subnet and MAC forwarding basics."""

from __future__ import annotations

import pytest

from pycie.protocols.ip_mac_basics import IPMacBasicsProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab06c]


def test_forward_decision_returns_no_route_when_destination_is_unknown() -> None:
    proc = IPMacBasicsProcess()
    proc.add_interface(if_name="eth0", prefix="10.0.0.1/24", mac="00:11:22:33:44:55")

    egress, mac, reason = proc.forward_decision("192.0.2.10")
    assert (egress, mac, reason) == (None, None, "no_route")


def test_connected_route_wins_tie_over_static_route() -> None:
    proc = IPMacBasicsProcess()
    proc.add_interface(if_name="eth0", prefix="10.0.0.1/24", mac="00:11:22:33:44:55")
    proc.add_static_route(prefix="10.0.0.0/24", next_hop="192.0.2.1", outgoing_interface="eth1")

    decision = proc.explain_lookup("10.0.0.50")
    assert decision is not None
    assert decision.connected is True
    assert decision.outgoing_interface == "eth0"


def test_static_route_tiebreak_is_deterministic_on_interface_name() -> None:
    proc = IPMacBasicsProcess()
    proc.add_interface(if_name="eth0", prefix="192.0.2.2/24", mac="00:00:00:00:00:01")
    proc.add_interface(if_name="eth1", prefix="198.51.100.2/24", mac="00:00:00:00:00:02")
    proc.add_static_route(prefix="203.0.113.0/24", next_hop="192.0.2.1", outgoing_interface="eth1")
    proc.add_static_route(prefix="203.0.113.0/24", next_hop="192.0.2.3", outgoing_interface="eth0")

    decision = proc.explain_lookup("203.0.113.7")
    assert decision is not None
    assert decision.outgoing_interface == "eth0"
    assert decision.next_hop_ip == "192.0.2.3"
