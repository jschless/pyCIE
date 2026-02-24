"""Exercise tests for Lab 22 ICMP control-plane basics."""

from __future__ import annotations

import pytest

from pycie.model.headers import ICMPHeader, ICMPv6Header, IPv4Header, IPv6Header
from pycie.protocols.icmp_control_plane_basics import (
    ICMPControlPlaneProcess,
    ICMPV6_TIME_EXCEEDED,
    ICMP_TIME_EXCEEDED,
)

pytestmark = [pytest.mark.exercise, pytest.mark.lab22]


def test_build_echo_request_ipv4_builds_expected_headers() -> None:
    proc = ICMPControlPlaneProcess()
    packet = proc.build_echo_request(src_ip="10.0.0.1", dst_ip="10.0.0.2", identifier=10, sequence=3, payload=b"ping")

    assert isinstance(packet.headers[0], IPv4Header)
    assert isinstance(packet.headers[1], ICMPHeader)
    assert packet.headers[1].icmp_type == 8
    assert packet.payload == b"ping"


def test_build_echo_reply_swaps_addresses_for_ipv4() -> None:
    proc = ICMPControlPlaneProcess()
    request = proc.build_echo_request(src_ip="10.1.1.1", dst_ip="10.1.1.2", payload=b"hello")
    reply = proc.build_echo_reply(request)

    ip = reply.headers[0]
    icmp = reply.headers[1]
    assert isinstance(ip, IPv4Header)
    assert isinstance(icmp, ICMPHeader)
    assert (ip.src_ip, ip.dst_ip) == ("10.1.1.2", "10.1.1.1")
    assert icmp.icmp_type == 0


def test_build_time_exceeded_ipv6_uses_icmpv6_type() -> None:
    proc = ICMPControlPlaneProcess()
    probe = proc.build_echo_request(src_ip="2001:db8::1", dst_ip="2001:db8::2", ipv6=True)
    response = proc.build_time_exceeded(probe, responder_ip="2001:db8::ffff")

    assert isinstance(response.headers[0], IPv6Header)
    assert isinstance(response.headers[1], ICMPv6Header)
    assert response.headers[1].icmp_type == ICMPV6_TIME_EXCEEDED


def test_traceroute_hop_result_distinguishes_transit_and_destination() -> None:
    proc = ICMPControlPlaneProcess()
    probe = proc.traceroute_probe(src_ip="10.0.0.10", dst_ip="10.0.0.99", ttl=3)

    mid = proc.traceroute_hop_result(probe, hop_index=2, destination_hop=4, responder_ip="10.0.0.2")
    end = proc.traceroute_hop_result(probe, hop_index=4, destination_hop=4, responder_ip="10.0.0.99")

    assert mid.outcome == "time_exceeded"
    assert mid.icmp_type == ICMP_TIME_EXCEEDED
    assert end.outcome == "destination_reached"
    assert end.icmp_type == 0
