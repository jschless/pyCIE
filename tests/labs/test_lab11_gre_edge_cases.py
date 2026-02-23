"""Edge-case tests for Lab 11 GRE."""

from __future__ import annotations

import pytest

from pycie.model.headers import GREHeader, IPv4Header
from pycie.model.packet import PacketStack
from pycie.protocols.gre import GRETunnelProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab11]


def test_decapsulate_rejects_non_gre_outer_protocol() -> None:
    proc = GRETunnelProcess()
    packet = PacketStack(
        headers=[
            IPv4Header(src_ip="192.0.2.1", dst_ip="192.0.2.2", protocol=6),
            GREHeader(protocol_type=0x0800, key=1),
        ]
    )

    assert proc.decapsulate(packet) == (None, None)


def test_unknown_tunnel_maps_to_default_id() -> None:
    proc = GRETunnelProcess()
    packet = PacketStack(
        headers=[
            IPv4Header(src_ip="192.0.2.9", dst_ip="192.0.2.10", protocol=47),
            GREHeader(protocol_type=0x0800, key=999),
            IPv4Header(src_ip="10.0.0.1", dst_ip="10.0.0.2", protocol=17),
        ]
    )

    tunnel_id, inner = proc.decapsulate(packet)
    assert tunnel_id == "default-gre"
    assert inner is not None
