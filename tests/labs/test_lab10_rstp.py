"""Exercise tests for Lab 10 RSTP."""

from __future__ import annotations

import pytest

from pycie.protocols.rstp import RSTPBPDU, RSTPBridgeId, RSTPPort, RSTPProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab10]


def _proc(priority: int, mac: str) -> RSTPProcess:
    p = RSTPProcess(bridge_priority=priority, bridge_mac=mac)
    p.ports = {
        "eth0": RSTPPort("eth0", 1),
        "eth1": RSTPPort("eth1", 2),
    }
    return p


def test_superior_root_updates_local_view() -> None:
    proc = _proc(32768, "00:00:00:00:00:0a")
    bpdu = RSTPBPDU(
        root_id=RSTPBridgeId(32768, "00:00:00:00:00:01"),
        cost=4,
        bridge_id=RSTPBridgeId(32768, "00:00:00:00:00:01"),
        port_id=1,
        proposal=True,
    )

    proc.process_bpdu("eth0", bpdu)
    assert proc.root_id == RSTPBridgeId(32768, "00:00:00:00:00:01")


def test_transmit_bpdu_reflects_flags() -> None:
    proc = _proc(32768, "00:00:00:00:00:0a")
    out = proc.transmit_bpdu("eth0", proposal=True, agreement=False)

    assert out.proposal is True
    assert out.agreement is False
