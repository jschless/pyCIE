"""Edge-case tests for Lab 15 MPLS forwarding."""

from __future__ import annotations

import pytest

from pycie.forwarding.mpls import LFIBEntry, MPLSForwarder
from pycie.model.headers import IPv4Header, MPLSLabel
from pycie.model.packet import PacketStack

pytestmark = [pytest.mark.exercise, pytest.mark.lab15]


def test_swap_operation_rewrites_top_label() -> None:
    fwd = MPLSForwarder()
    fwd.install_entry(LFIBEntry(in_label=100, out_label=200, egress_if="eth1", operation="swap"))
    packet = PacketStack(headers=[MPLSLabel(label=100), IPv4Header(src_ip="10.0.0.1", dst_ip="10.0.0.2", protocol=6)])

    egress, out, reason = fwd.forward(packet)
    assert egress == "eth1"
    assert reason is None
    assert isinstance(out, PacketStack)
    assert isinstance(out.headers[0], MPLSLabel)
    assert out.headers[0].label == 200


def test_push_without_out_label_drops_packet() -> None:
    fwd = MPLSForwarder()
    fwd.install_entry(LFIBEntry(in_label=None, out_label=None, egress_if="eth1", operation="push"))
    packet = PacketStack(headers=[IPv4Header(src_ip="10.0.0.1", dst_ip="10.0.0.2", protocol=6)])

    assert fwd.forward(packet) == (None, None, "missing_out_label")
