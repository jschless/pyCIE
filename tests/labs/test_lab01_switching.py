"""Exercise tests for Lab 01 learning switch."""

from __future__ import annotations

from pycie.core.node import Device
from pycie.protocols.switching import LearningSwitch, MacEntry
from pycie.sim.network import Interface, NetworkSimulator, Topology
import pytest

pytestmark = [pytest.mark.exercise, pytest.mark.lab01]


def _build_switch() -> tuple[NetworkSimulator, Device, LearningSwitch]:
    topo = Topology()
    topo.add_node("sw1")
    for if_name, mac in (("eth0", "02:00:00:00:00:01"), ("eth1", "02:00:00:00:00:02"), ("eth2", "02:00:00:00:00:03")):
        iface = Interface("sw1", if_name, mac)
        topo.add_interface(iface)

    sim = NetworkSimulator(topology=topo)
    sw_dev = Device("sw1", sim)
    for iface in topo.interfaces.values():
        sw_dev.add_interface(iface)

    l2 = LearningSwitch()
    sw_dev.register_protocol("l2", l2)
    return sim, sw_dev, l2


def test_learn_source_mac_creates_or_refreshes_entry() -> None:
    sim, _dev, l2 = _build_switch()

    l2.learn_source_mac("eth1", "aa:bb:cc:dd:ee:01")
    assert l2.mac_table["aa:bb:cc:dd:ee:01"].interface == "eth1"

    sim.clock.advance_by(50)
    l2.learn_source_mac("eth2", "aa:bb:cc:dd:ee:01")
    assert l2.mac_table["aa:bb:cc:dd:ee:01"].interface == "eth2"
    assert l2.mac_table["aa:bb:cc:dd:ee:01"].learned_at_ms == 50


def test_lookup_unknown_unicast_floods_except_ingress() -> None:
    _sim, _dev, l2 = _build_switch()

    egress = l2.lookup_egress_interfaces("eth1", "aa:bb:cc:dd:ee:ff")
    assert sorted(egress) == ["eth0", "eth2"]


def test_lookup_known_unicast_returns_single_egress() -> None:
    _sim, _dev, l2 = _build_switch()

    l2.mac_table["aa:bb:cc:dd:ee:ff"] = MacEntry(
        mac="aa:bb:cc:dd:ee:ff",
        interface="eth2",
        learned_at_ms=0,
    )

    egress = l2.lookup_egress_interfaces("eth0", "aa:bb:cc:dd:ee:ff")
    assert egress == ["eth2"]


def test_age_mac_table_expires_old_entries() -> None:
    sim, _dev, l2 = _build_switch()

    l2.mac_table["old"] = MacEntry(mac="old", interface="eth0", learned_at_ms=0)
    l2.mac_table["new"] = MacEntry(mac="new", interface="eth1", learned_at_ms=10)

    sim.clock.advance_to(11)
    l2.mac_aging_ms = 10
    l2.age_mac_table()

    assert "old" not in l2.mac_table
    assert "new" in l2.mac_table


def test_should_flood_for_broadcast_and_unknown_only() -> None:
    _sim, _dev, l2 = _build_switch()
    l2.mac_table["aa:aa:aa:aa:aa:aa"] = MacEntry("aa:aa:aa:aa:aa:aa", "eth0", 0)

    assert l2.should_flood("ff:ff:ff:ff:ff:ff")
    assert l2.should_flood("00:11:22:33:44:55")
    assert not l2.should_flood("aa:aa:aa:aa:aa:aa")
