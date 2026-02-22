"""Exercise tests for Lab 35 VXLAN overlay data plane."""

from __future__ import annotations

import pytest

from pycie.protocols.vxlan import VXLANBridge
from pycie.sim.network import Frame

pytestmark = [pytest.mark.exercise, pytest.mark.lab35]


def _frame(src: str = "00:11:22:33:44:55", dst: str = "66:77:88:99:aa:bb") -> Frame:
    return Frame(src_mac=src, dst_mac=dst, ethertype="0x0800", payload=b"data")


def test_unknown_unicast_floods_local_and_remote_sorted() -> None:
    bridge = VXLANBridge(local_vtep_ip="198.51.100.10")
    bridge.add_access_port(5000, "eth2")
    bridge.add_access_port(5000, "eth1")
    bridge.add_remote_vtep(5000, "198.51.100.20")
    bridge.add_remote_vtep(5000, "198.51.100.30")

    egress = bridge.lookup_egress(5000, "eth1", "00:aa:bb:cc:dd:ee")
    assert egress == ["eth2", "vtep:198.51.100.20", "vtep:198.51.100.30"]


def test_flood_excludes_ingress_interface() -> None:
    bridge = VXLANBridge(local_vtep_ip="198.51.100.10")
    bridge.add_access_port(5000, "eth1")
    bridge.add_access_port(5000, "eth2")

    egress = bridge.lookup_egress(5000, "eth2", "ff:ff:ff:ff:ff:ff")
    assert egress == ["eth1"]


def test_known_local_unicast_returns_single_interface() -> None:
    bridge = VXLANBridge(local_vtep_ip="198.51.100.10")
    bridge.learn_local(5000, "00:11:22:33:44:55", "eth9")

    assert bridge.lookup_egress(5000, "eth1", "00:11:22:33:44:55") == ["eth9"]


def test_known_local_on_ingress_returns_empty() -> None:
    bridge = VXLANBridge(local_vtep_ip="198.51.100.10")
    bridge.learn_local(5000, "00:11:22:33:44:55", "eth9")

    assert bridge.lookup_egress(5000, "eth9", "00:11:22:33:44:55") == []


def test_known_remote_unicast_returns_vtep_target() -> None:
    bridge = VXLANBridge(local_vtep_ip="198.51.100.10")
    bridge.learn_remote(5000, "00:11:22:33:44:55", "198.51.100.200")

    assert bridge.lookup_egress(5000, "eth1", "00:11:22:33:44:55") == ["vtep:198.51.100.200"]


def test_vni_isolation_prevents_cross_tenant_learning() -> None:
    bridge = VXLANBridge(local_vtep_ip="198.51.100.10")
    bridge.learn_local(5000, "00:11:22:33:44:55", "eth1")

    assert bridge.lookup_egress(6000, "eth9", "00:11:22:33:44:55") == []


def test_encapsulate_and_decapsulate_round_trip() -> None:
    bridge = VXLANBridge(local_vtep_ip="198.51.100.10")
    frame = _frame()

    packet = bridge.encapsulate(5000, "198.51.100.20", frame)
    out = bridge.decapsulate(packet)

    assert packet.header.vni == 5000
    assert packet.header.src_vtep == "198.51.100.10"
    assert out == frame


def test_broadcast_floods_even_when_destination_is_known_unicast() -> None:
    bridge = VXLANBridge(local_vtep_ip="198.51.100.10")
    bridge.learn_local(5000, "00:11:22:33:44:55", "eth7")
    bridge.add_access_port(5000, "eth7")
    bridge.add_access_port(5000, "eth8")

    egress = bridge.lookup_egress(5000, "eth7", "ff:ff:ff:ff:ff:ff")
    assert egress == ["eth8"]
