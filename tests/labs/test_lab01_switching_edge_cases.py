"""Edge-case tests for Lab 01 learning switch."""

from __future__ import annotations

import pytest

from pycie.core.node import Device
from pycie.protocols.switching import LearningSwitch, MacEntry
from pycie.sim.network import Interface, NetworkSimulator, Topology

pytestmark = [pytest.mark.exercise, pytest.mark.lab01]


def _build_switch() -> LearningSwitch:
    topo = Topology()
    topo.add_node("sw1")
    for if_name, mac in (
        ("eth0", "02:00:00:00:00:01"),
        ("eth1", "02:00:00:00:00:02"),
        ("eth2", "02:00:00:00:00:03"),
    ):
        topo.add_interface(Interface("sw1", if_name, mac))

    sim = NetworkSimulator(topology=topo)
    dev = Device("sw1", sim)
    for iface in topo.interfaces.values():
        dev.add_interface(iface)

    proc = LearningSwitch()
    dev.register_protocol("l2", proc)
    return proc


def test_known_unicast_on_ingress_interface_is_not_forwarded() -> None:
    sw = _build_switch()
    sw.mac_table["aa:bb:cc:dd:ee:ff"] = MacEntry("aa:bb:cc:dd:ee:ff", "eth1", 0)

    assert sw.lookup_egress_interfaces("eth1", "aa:bb:cc:dd:ee:ff") == []
