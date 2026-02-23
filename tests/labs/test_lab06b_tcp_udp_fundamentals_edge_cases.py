"""Edge-case tests for Lab 06b TCP/UDP fundamentals."""

from __future__ import annotations

import pytest

from pycie.model.headers import IPv4Header
from pycie.model.packet import PacketStack
from pycie.protocols.tcp_udp_fundamentals import (
    TCPConnection,
    TCPSegment,
    TCPState,
    TransportFundamentalsProcess,
    validate_tcp_segment,
)

pytestmark = [pytest.mark.exercise, pytest.mark.lab06b]


def test_validate_tcp_segment_rejects_syn_fin_combination() -> None:
    segment = TCPSegment(src_port=1234, dst_port=80, flags=frozenset({"syn", "fin"}))
    assert validate_tcp_segment(segment) is False


def test_receive_reset_always_closes_connection() -> None:
    conn = TCPConnection(state=TCPState.ESTABLISHED)

    result = conn.receive(TCPSegment(src_port=80, dst_port=1234, flags=frozenset({"rst"})))
    assert result == "reset"
    assert conn.state == TCPState.CLOSED


def test_invalid_segment_does_not_change_state() -> None:
    conn = TCPConnection(state=TCPState.SYN_SENT)

    result = conn.receive(TCPSegment(src_port=80, dst_port=1234, flags=frozenset({"bad_flag"})))
    assert result == "invalid_segment"
    assert conn.state == TCPState.SYN_SENT


def test_extract_flow_tuple_returns_none_without_transport_header() -> None:
    proc = TransportFundamentalsProcess()
    packet = PacketStack(headers=[IPv4Header(src_ip="10.0.0.1", dst_ip="10.0.0.2", protocol=1)])

    assert proc.extract_flow_tuple(packet) is None
