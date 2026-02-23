"""Exercise tests for Lab 06a packet construction."""

from __future__ import annotations

import pytest

from pycie.model.headers import Dot1QHeader, EthernetHeader, IPv4Header, UDPHeader
from pycie.model.packet import PacketStack
from pycie.protocols.packet_construction import PacketConstructionProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab06a]


def test_build_ipv4_udp_derives_udp_length_from_payload() -> None:
    proc = PacketConstructionProcess()
    packet = proc.build_ipv4_udp(
        src_mac="aa:aa:aa:aa:aa:01",
        dst_mac="bb:bb:bb:bb:bb:02",
        src_ip="10.0.0.1",
        dst_ip="10.0.0.2",
        src_port=12000,
        dst_port=53,
        payload=b"hello",
    )

    assert isinstance(packet.headers[0], EthernetHeader)
    assert isinstance(packet.headers[1], IPv4Header)
    udp = packet.headers[2]
    assert isinstance(udp, UDPHeader)
    assert udp.length == 13


def test_insert_vlan_tag_places_dot1q_after_ethernet() -> None:
    proc = PacketConstructionProcess()
    packet = proc.build_ipv4_udp(
        src_mac="aa:aa:aa:aa:aa:01",
        dst_mac="bb:bb:bb:bb:bb:02",
        src_ip="10.0.0.1",
        dst_ip="10.0.0.2",
        src_port=12000,
        dst_port=53,
        payload=b"hello",
    )

    tagged = proc.insert_vlan_tag(packet, vlan_id=200, pcp=5)
    assert isinstance(tagged.headers[0], EthernetHeader)
    assert isinstance(tagged.headers[1], Dot1QHeader)
    assert tagged.headers[1].vlan_id == 200


def test_normalize_transport_lengths_fixes_udp_length() -> None:
    proc = PacketConstructionProcess()
    packet = PacketStack(
        headers=[
            EthernetHeader(dst_mac="bb", src_mac="aa", ethertype="0x0800"),
            IPv4Header(src_ip="10.0.0.1", dst_ip="10.0.0.2", protocol=17),
            UDPHeader(src_port=1111, dst_port=2222, length=0),
        ],
        payload=b"abcd",
    )

    normalized = proc.normalize_transport_lengths(packet)
    udp = normalized.headers[2]
    assert isinstance(udp, UDPHeader)
    assert udp.length == 12


def test_build_packet_rejects_invalid_stack_order() -> None:
    proc = PacketConstructionProcess()
    with pytest.raises(ValueError, match="invalid_order"):
        proc.build_packet(
            [
                IPv4Header(src_ip="10.0.0.1", dst_ip="10.0.0.2", protocol=17),
                EthernetHeader(dst_mac="bb", src_mac="aa", ethertype="0x0800"),
            ],
            payload=b"x",
        )
