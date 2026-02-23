"""Edge-case tests for Lab 35 VXLAN overlay data plane."""

from __future__ import annotations

import pytest

from pycie.protocols.vxlan import VXLANBridge

pytestmark = [pytest.mark.exercise, pytest.mark.lab35]


def test_lookup_is_case_insensitive_for_destination_mac() -> None:
    bridge = VXLANBridge(local_vtep_ip="198.51.100.10")
    bridge.learn_local(5000, "00:11:22:33:44:55", "eth1")

    assert bridge.lookup_egress(5000, "eth9", "00:11:22:33:44:55") == ["eth1"]
    assert bridge.lookup_egress(5000, "eth9", "00:11:22:33:44:55".upper()) == ["eth1"]


def test_lookup_unknown_vni_with_no_ports_returns_empty_list() -> None:
    bridge = VXLANBridge(local_vtep_ip="198.51.100.10")
    assert bridge.lookup_egress(7777, "eth0", "de:ad:be:ef:00:01") == []

