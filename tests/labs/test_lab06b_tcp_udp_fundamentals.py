"""Exercise tests for Lab 06b TCP/UDP fundamentals."""

from __future__ import annotations

import pytest

from pycie.model.headers import IPv4Header, TCPHeader, UDPHeader
from pycie.model.packet import PacketStack
from pycie.protocols.tcp_udp_fundamentals import TCPConnection, TCPSegment, TCPState, TransportFundamentalsProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab06b]


def test_tcp_session_handshake_reaches_established() -> None:
    proc = TransportFundamentalsProcess()

    syn = proc.open_session("flow1", src_port=49152, dst_port=179)
    assert syn.flags == frozenset({"syn"})

    result = proc.receive_segment("flow1", TCPSegment(src_port=179, dst_port=49152, flags=frozenset({"syn", "ack"})))
    assert result == "syn_ack_received"
    assert proc.sessions["flow1"].state == TCPState.ESTABLISHED


def test_close_session_transitions_to_fin_wait_then_closed() -> None:
    proc = TransportFundamentalsProcess()
    proc.sessions["flow1"] = TCPConnection(state=TCPState.ESTABLISHED)

    fin = proc.close_session("flow1", src_port=49152, dst_port=80)
    assert fin.flags == frozenset({"fin", "ack"})
    assert proc.sessions["flow1"].state == TCPState.FIN_WAIT

    result = proc.receive_segment("flow1", TCPSegment(src_port=80, dst_port=49152, flags=frozenset({"ack"})))
    assert result == "close_complete"
    assert proc.sessions["flow1"].state == TCPState.CLOSED


def test_extract_flow_tuple_from_packet_stack() -> None:
    proc = TransportFundamentalsProcess()
    packet = PacketStack(
        headers=[
            IPv4Header(src_ip="10.0.0.1", dst_ip="10.0.0.2", protocol=6),
            TCPHeader(src_port=12345, dst_port=443, flags=frozenset({"syn"})),
        ]
    )

    assert proc.extract_flow_tuple(packet) == ("tcp", "10.0.0.1", "10.0.0.2", 12345, 443)


def test_udp_checksum_changes_when_payload_changes() -> None:
    proc = TransportFundamentalsProcess()
    h1 = UDPHeader(src_port=12000, dst_port=53, length=13)
    h2 = UDPHeader(src_port=12000, dst_port=53, length=14)

    c1 = proc.compute_udp_checksum(src_ip="192.0.2.1", dst_ip="198.51.100.1", udp_header=h1, payload=b"hello")
    c2 = proc.compute_udp_checksum(src_ip="192.0.2.1", dst_ip="198.51.100.1", udp_header=h2, payload=b"hello!")

    assert c1 != c2
