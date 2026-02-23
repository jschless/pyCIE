"""Exercise tests for Lab 06c IP subnet and MAC forwarding basics."""

from __future__ import annotations

import pytest

from pycie.protocols.ip_mac_basics import IPMacBasicsProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab06c]


def test_lookup_prefers_longest_prefix_match() -> None:
    proc = IPMacBasicsProcess()
    proc.add_interface(if_name="eth0", prefix="10.0.0.1/24", mac="00:11:22:33:44:55")
    proc.add_static_route(prefix="10.0.0.0/16", next_hop="192.0.2.1", outgoing_interface="eth1")

    decision = proc.explain_lookup("10.0.0.42")
    assert decision is not None
    assert decision.selected_prefix == "10.0.0.0/24"
    assert decision.connected is True


def test_forward_decision_requires_arp_then_forwards_after_learning() -> None:
    proc = IPMacBasicsProcess()
    proc.add_interface(if_name="eth0", prefix="10.0.0.1/24", mac="00:11:22:33:44:55")

    egress, mac, reason = proc.forward_decision("10.0.0.99")
    assert (egress, mac, reason) == ("eth0", None, "mac_unresolved")

    proc.learn_arp(ip="10.0.0.99", mac="aa:bb:cc:dd:ee:ff")
    egress, mac, reason = proc.forward_decision("10.0.0.99")
    assert (egress, mac, reason) == ("eth0", "aa:bb:cc:dd:ee:ff", None)


def test_static_route_uses_next_hop_for_mac_resolution() -> None:
    proc = IPMacBasicsProcess()
    proc.add_interface(if_name="eth1", prefix="172.16.0.1/24", mac="00:11:22:33:44:66")
    proc.add_static_route(prefix="203.0.113.0/24", next_hop="172.16.0.2", outgoing_interface="eth1")

    proc.learn_arp(ip="172.16.0.2", mac="de:ad:be:ef:00:01")
    egress, mac, reason = proc.forward_decision("203.0.113.9")
    assert (egress, mac, reason) == ("eth1", "de:ad:be:ef:00:01", None)


def test_prefix_details_reports_mask_fields() -> None:
    proc = IPMacBasicsProcess()
    details = proc.prefix_details("10.10.10.1/24")

    assert details["network"] == "10.10.10.0"
    assert details["netmask"] == "255.255.255.0"
    assert details["prefix_length"] == 24
