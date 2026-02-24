"""Edge-case tests for Lab 22 ICMP control-plane basics."""

from __future__ import annotations

import pytest

from pycie.model.headers import ICMPHeader, IPv4Header
from pycie.model.packet import PacketStack
from pycie.protocols.icmp_control_plane_basics import ICMPControlPlaneProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab22]


def test_build_echo_reply_rejects_non_echo_request() -> None:
    proc = ICMPControlPlaneProcess()
    packet = PacketStack(
        headers=[
            IPv4Header(src_ip="10.0.0.1", dst_ip="10.0.0.2", protocol=1),
            ICMPHeader(icmp_type=3, icmp_code=1),
        ]
    )

    with pytest.raises(ValueError, match="not_icmp_echo_request"):
        proc.build_echo_reply(packet)


def test_traceroute_probe_requires_positive_ttl() -> None:
    proc = ICMPControlPlaneProcess()
    with pytest.raises(ValueError, match="ttl_must_be_positive"):
        proc.traceroute_probe(src_ip="10.0.0.1", dst_ip="10.0.0.2", ttl=0)


def test_build_destination_unreachable_ipv4_defaults_to_code_zero() -> None:
    proc = ICMPControlPlaneProcess()
    probe = proc.traceroute_probe(src_ip="10.0.0.1", dst_ip="10.0.0.2", ttl=1)
    response = proc.build_destination_unreachable(probe, responder_ip="10.0.0.254")

    icmp = response.headers[1]
    assert isinstance(icmp, ICMPHeader)
    assert icmp.icmp_type == 3
    assert icmp.icmp_code == 0
