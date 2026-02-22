"""Exercise tests for Lab 15 MPLS forwarding."""

from __future__ import annotations

import pytest

from pycie.forwarding.mpls import LFIBEntry, MPLSForwarder
from pycie.model.headers import IPv4Header, MPLSLabel
from pycie.model.packet import PacketStack
from pycie.protocols.mpls import MPLSProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab15]


def test_mpls_forwarder_pushes_label_when_entry_requires_push() -> None:
    fwd = MPLSForwarder()
    fwd.install_entry(LFIBEntry(in_label=None, out_label=16000, egress_if="eth0", operation="push"))

    pkt = PacketStack(headers=[IPv4Header(src_ip="10.0.0.1", dst_ip="10.0.0.2", protocol=6)])
    egress, out, reason = fwd.forward(pkt)

    assert egress == "eth0"
    assert out is not None
    assert out.has_header(MPLSLabel)
    assert reason is None


def test_mpls_process_builds_lfib_from_bindings() -> None:
    proc = MPLSProcess()
    local = proc.allocate_label("10.10.10.0/24")
    proc.install_remote_binding("2.2.2.2", "10.10.10.0/24", 24000)

    lfib = proc.build_lfib_view()
    assert lfib["10.10.10.0/24"] == (24000, local)
