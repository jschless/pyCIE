"""Exercise tests for Lab 11 GRE."""

from __future__ import annotations

import pytest

from pycie.forwarding.encapsulation import EncapsulationPipeline, TunnelConfig
from pycie.model.headers import GREHeader, IPv4Header
from pycie.model.packet import PacketStack
from pycie.protocols.gre import GRETunnel, GRETunnelProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab11]


def test_encapsulation_pipeline_adds_outer_ipv4_and_gre() -> None:
    pipe = EncapsulationPipeline()
    inner = PacketStack(headers=[IPv4Header(src_ip="10.0.0.1", dst_ip="10.0.0.2", protocol=6)])
    cfg = TunnelConfig(tunnel_src="192.0.2.1", tunnel_dst="192.0.2.2", mode="gre", key=99)

    out = pipe.encapsulate(inner, cfg)
    assert isinstance(out.headers[0], IPv4Header)
    assert isinstance(out.headers[1], GREHeader)


def test_gre_process_roundtrip() -> None:
    proc = GRETunnelProcess()
    tun = GRETunnel("tun1", source_ip="192.0.2.1", destination_ip="192.0.2.2", key=123)
    inner = PacketStack(headers=[IPv4Header(src_ip="10.0.0.1", dst_ip="10.0.0.2", protocol=17)])

    enc = proc.encapsulate(tun, inner)
    tunnel_id, dec = proc.decapsulate(enc)

    assert tunnel_id == "tun1"
    assert dec is not None
