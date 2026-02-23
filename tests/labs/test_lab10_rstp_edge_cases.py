"""Edge-case tests for Lab 10 RSTP."""

from __future__ import annotations

import pytest

from pycie.protocols.rstp import RSTPBPDU, RSTPBridgeId, RSTPPort, RSTPProcess, RSTPState

pytestmark = [pytest.mark.exercise, pytest.mark.lab10]


def test_unknown_port_bpdu_is_ignored() -> None:
    proc = RSTPProcess(bridge_priority=32768, bridge_mac="00:00:00:00:00:0a")
    proc.ports = {"eth0": RSTPPort("eth0", 1)}
    before = (proc.root_id, proc.root_port)

    bpdu = RSTPBPDU(
        root_id=RSTPBridgeId(32768, "00:00:00:00:00:01"),
        cost=4,
        bridge_id=RSTPBridgeId(32768, "00:00:00:00:00:01"),
        port_id=1,
    )
    proc.process_bpdu("eth99", bpdu)

    assert (proc.root_id, proc.root_port) == before


def test_non_agreement_bpdu_keeps_port_discarding() -> None:
    proc = RSTPProcess(bridge_priority=32768, bridge_mac="00:00:00:00:00:0a")
    proc.ports = {"eth0": RSTPPort("eth0", 1)}

    bpdu = RSTPBPDU(
        root_id=proc.root_id,
        cost=0,
        bridge_id=proc.bridge_id,
        port_id=1,
        proposal=False,
        agreement=False,
    )
    proc.process_bpdu("eth0", bpdu)

    assert proc.ports["eth0"].state == RSTPState.DISCARDING
