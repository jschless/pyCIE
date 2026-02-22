"""Exercise tests for Lab 09 VLAN forwarding."""

from __future__ import annotations

import pytest

from pycie.forwarding.l2 import BridgeDomain, BridgePort
from pycie.model.headers import Dot1QHeader, EthernetHeader
from pycie.model.packet import PacketStack

pytestmark = [pytest.mark.exercise, pytest.mark.lab09]


def _packet(src: str, dst: str, vlan: int | None) -> PacketStack:
    headers = [EthernetHeader(dst_mac=dst, src_mac=src, ethertype="0x0800")]
    if vlan is not None:
        headers.insert(1, Dot1QHeader(vlan_id=vlan))
    return PacketStack(headers=headers, payload=b"x")


def test_access_port_ingress_vlan_mapping() -> None:
    bd = BridgeDomain()
    bd.register_port(BridgePort("eth0", mode="access", access_vlan=10))

    vlan = bd.ingress_vlan("eth0", _packet("aa", "bb", None))
    assert vlan == 10


def test_trunk_rejects_disallowed_vlan() -> None:
    bd = BridgeDomain()
    bd.register_port(BridgePort("eth1", mode="trunk", allowed_vlans=frozenset({10, 20}), native_vlan=10))

    vlan = bd.ingress_vlan("eth1", _packet("aa", "bb", 30))
    assert vlan is None


def test_lookup_egress_scoped_to_vlan() -> None:
    bd = BridgeDomain()
    bd.register_port(BridgePort("eth0", mode="access", access_vlan=10))
    bd.register_port(BridgePort("eth1", mode="access", access_vlan=10))
    bd.register_port(BridgePort("eth2", mode="access", access_vlan=20))

    bd.learn(10, "00:00:00:00:00:ff", "eth1", now_ms=0)
    egress = bd.lookup_egress(10, "00:00:00:00:00:ff", "eth0")
    assert egress == ["eth1"]


def test_egress_tag_decision_on_trunk_native_vlan() -> None:
    bd = BridgeDomain()
    bd.register_port(BridgePort("eth9", mode="trunk", allowed_vlans=frozenset({10, 20}), native_vlan=10))

    assert not bd.egress_should_tag("eth9", 10)
    assert bd.egress_should_tag("eth9", 20)
