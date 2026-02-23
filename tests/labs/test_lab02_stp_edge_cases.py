"""Edge-case tests for Lab 02 STP."""

from __future__ import annotations

import pytest

from pycie.protocols.stp import STPPort, STPProcess
from pycie.sim.network import Frame

pytestmark = [pytest.mark.exercise, pytest.mark.lab02]


def test_on_frame_ignores_non_bpdu_payload() -> None:
    stp = STPProcess(bridge_priority=32768, bridge_mac="00:00:00:00:00:0a")
    stp.ports = {"eth0": STPPort("eth0", 1), "eth1": STPPort("eth1", 2)}
    before = (stp.root_id, stp.root_cost, stp.root_port)

    stp.on_frame("eth0", Frame(src_mac="aa", dst_mac="bb", ethertype="0x0800", payload=b"not-bpdu"))

    assert (stp.root_id, stp.root_cost, stp.root_port) == before
