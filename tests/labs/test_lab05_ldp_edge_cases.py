"""Edge-case tests for Lab 05 LDP."""

from __future__ import annotations

import pytest

from pycie.protocols.ldp import LDPHello, LDPProcess
from pycie.sim.network import Frame

pytestmark = [pytest.mark.exercise, pytest.mark.lab05]


def test_on_frame_hello_creates_up_neighbor() -> None:
    ldp = LDPProcess(router_id="1.1.1.1")
    hello = LDPHello(router_id="2.2.2.2")

    ldp.on_frame("eth0", Frame(src_mac="aa", dst_mac="bb", ethertype="0x8847", payload=hello))
    assert ldp.neighbors["2.2.2.2"].state == "UP"


def test_lfib_uses_local_label_when_remote_missing() -> None:
    ldp = LDPProcess(router_id="1.1.1.1")
    label = ldp.allocate_local_label("10.0.0.0/24")

    lfib = ldp.build_lfib()
    assert lfib["10.0.0.0/24"] == (label, label)
