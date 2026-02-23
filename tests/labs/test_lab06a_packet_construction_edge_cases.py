"""Edge-case tests for Lab 06a packet construction."""

from __future__ import annotations

import pytest

from pycie.model.headers import Dot1QHeader, EthernetHeader, TCPHeader
from pycie.model.packet import PacketStack
from pycie.protocols.packet_construction import PacketConstructionProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab06a]


def test_insert_vlan_requires_outer_ethernet_header() -> None:
    proc = PacketConstructionProcess()
    packet = PacketStack(headers=[TCPHeader(src_port=1, dst_port=2)], payload=b"")

    with pytest.raises(ValueError, match="missing_outer_ethernet"):
        proc.insert_vlan_tag(packet, vlan_id=10)


def test_validate_packet_rejects_dot1q_without_ethernet() -> None:
    proc = PacketConstructionProcess()
    packet = PacketStack(headers=[Dot1QHeader(vlan_id=100), EthernetHeader(dst_mac="bb", src_mac="aa", ethertype="0x0800")])

    valid, reason = proc.validate_packet(packet)
    assert valid is False
    assert reason == "dot1q_without_outer_ethernet"


def test_validate_packet_rejects_l4_without_l3() -> None:
    proc = PacketConstructionProcess()
    packet = PacketStack(
        headers=[
            EthernetHeader(dst_mac="bb", src_mac="aa", ethertype="0x0800"),
            TCPHeader(src_port=12345, dst_port=443),
        ]
    )

    valid, reason = proc.validate_packet(packet)
    assert valid is False
    assert reason == "l4_without_l3"
