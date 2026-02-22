"""Exercise tests for Lab 02 STP."""

from __future__ import annotations

import pytest

from pycie.protocols.stp import BPDU, BridgeId, STPPort, STPProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab02]


def _make_proc(priority: int, mac: str) -> STPProcess:
    proc = STPProcess(bridge_priority=priority, bridge_mac=mac)
    proc.ports = {
        "eth0": STPPort(if_name="eth0", port_id=1),
        "eth1": STPPort(if_name="eth1", port_id=2),
    }
    return proc


def test_superior_bpdu_updates_root_view() -> None:
    proc = _make_proc(32768, "00:00:00:00:00:0a")

    superior = BPDU(
        root_id=BridgeId(32768, "00:00:00:00:00:01"),
        root_path_cost=4,
        bridge_id=BridgeId(32768, "00:00:00:00:00:01"),
        port_id=1,
    )

    proc.process_bpdu("eth0", superior)
    assert proc.root_id == BridgeId(32768, "00:00:00:00:00:01")
    assert proc.root_port == "eth0"


def test_inferior_bpdu_does_not_override_better_root() -> None:
    proc = _make_proc(32768, "00:00:00:00:00:0a")
    proc.root_id = BridgeId(32768, "00:00:00:00:00:01")
    proc.root_port = "eth0"

    inferior = BPDU(
        root_id=BridgeId(32768, "00:00:00:00:00:ff"),
        root_path_cost=1,
        bridge_id=BridgeId(32768, "00:00:00:00:00:ff"),
        port_id=9,
    )

    proc.process_bpdu("eth1", inferior)
    assert proc.root_id == BridgeId(32768, "00:00:00:00:00:01")
    assert proc.root_port == "eth0"


def test_recompute_port_states_sets_root_and_blocks_non_designated() -> None:
    proc = _make_proc(32768, "00:00:00:00:00:0a")
    proc.root_id = BridgeId(32768, "00:00:00:00:00:01")
    proc.root_port = "eth0"

    proc.recompute_port_states()

    assert proc.ports["eth0"].role == "ROOT"
    assert proc.ports["eth0"].state == "FORWARDING"
    assert proc.ports["eth1"].state in {"BLOCKING", "FORWARDING"}


def test_should_forward_data_true_only_when_forwarding() -> None:
    proc = _make_proc(32768, "00:00:00:00:00:0a")
    proc.ports["eth0"].state = "FORWARDING"
    proc.ports["eth1"].state = "BLOCKING"

    assert proc.should_forward_data("eth0")
    assert not proc.should_forward_data("eth1")
