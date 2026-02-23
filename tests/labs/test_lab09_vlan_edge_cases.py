"""Edge-case tests for Lab 09 VLAN forwarding."""

from __future__ import annotations

import pytest

from pycie.forwarding.l2 import BridgeDomain, BridgePort
from pycie.model.headers import Dot1QHeader, EthernetHeader
from pycie.model.packet import PacketStack

pytestmark = [pytest.mark.exercise, pytest.mark.lab09]


def test_access_port_drops_tagged_ingress_frame() -> None:
    bd = BridgeDomain()
    bd.register_port(BridgePort("eth0", mode="access", access_vlan=10))
    tagged = PacketStack(
        headers=[
            EthernetHeader(dst_mac="bb", src_mac="aa", ethertype="0x0800"),
            Dot1QHeader(vlan_id=10),
        ],
        payload=b"x",
    )

    assert bd.ingress_vlan("eth0", tagged) is None


def test_trunk_untagged_without_native_vlan_is_dropped() -> None:
    bd = BridgeDomain()
    bd.register_port(BridgePort("eth1", mode="trunk", allowed_vlans=frozenset({10}), native_vlan=None))
    untagged = PacketStack(headers=[EthernetHeader(dst_mac="bb", src_mac="aa", ethertype="0x0800")], payload=b"x")

    assert bd.ingress_vlan("eth1", untagged) is None
