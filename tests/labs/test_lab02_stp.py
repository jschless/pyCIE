"""Exercise tests for Lab 02 STP."""

from __future__ import annotations

import pytest

from pycie.protocols.stp import BPDU, BridgeId, STPPort, STPProcess, STPRole, STPState

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


def test_on_start_resets_root_view_and_port_states() -> None:
    proc = _make_proc(32768, "00:00:00:00:00:0a")
    proc.root_id = BridgeId(32768, "00:00:00:00:00:01")
    proc.root_cost = 99
    proc.root_port = "eth1"
    proc.ports["eth0"].role = STPRole.ROOT
    proc.ports["eth0"].state = STPState.BLOCKING
    proc.ports["eth1"].role = STPRole.ALTERNATE
    proc.ports["eth1"].state = STPState.BLOCKING

    proc.on_start()

    assert proc.root_id == proc.bridge_id
    assert proc.root_cost == 0
    assert proc.root_port is None
    for port in proc.ports.values():
        assert port.role == STPRole.DESIGNATED
        assert port.state == STPState.FORWARDING


def test_process_bpdu_triggers_recompute_for_role_change() -> None:
    proc = _make_proc(32768, "00:00:00:00:00:0a")

    superior = BPDU(
        root_id=BridgeId(32768, "00:00:00:00:00:01"),
        root_path_cost=4,
        bridge_id=BridgeId(32768, "00:00:00:00:00:01"),
        port_id=1,
    )
    proc.process_bpdu("eth1", superior)

    assert proc.root_port == "eth1"
    assert proc.ports["eth1"].role == STPRole.ROOT
    assert proc.ports["eth1"].state == STPState.FORWARDING
    assert proc.ports["eth0"].state == STPState.BLOCKING


def test_root_port_selection_does_not_use_lowest_local_path_cost_only() -> None:
    proc = _make_proc(32768, "00:00:00:00:00:0a")
    proc.ports["eth0"].path_cost = 1
    proc.ports["eth1"].path_cost = 20

    superior_on_high_cost_port = BPDU(
        root_id=BridgeId(32768, "00:00:00:00:00:01"),
        root_path_cost=1,
        bridge_id=BridgeId(32768, "00:00:00:00:00:01"),
        port_id=1,
    )
    proc.process_bpdu("eth1", superior_on_high_cost_port)

    assert proc.root_port == "eth1"
    assert proc.ports["eth1"].role == STPRole.ROOT


def test_tie_break_prefers_lower_sender_bridge_then_sender_port() -> None:
    proc = _make_proc(32768, "00:00:00:00:00:0a")
    proc.root_id = BridgeId(32768, "00:00:00:00:00:01")
    proc.root_cost = 10
    proc.root_port = "eth0"

    better_bridge = BPDU(
        root_id=BridgeId(32768, "00:00:00:00:00:01"),
        root_path_cost=6,
        bridge_id=BridgeId(32768, "00:00:00:00:00:02"),
        port_id=20,
    )
    worse_bridge = BPDU(
        root_id=BridgeId(32768, "00:00:00:00:00:01"),
        root_path_cost=6,
        bridge_id=BridgeId(32768, "00:00:00:00:00:03"),
        port_id=1,
    )

    proc.process_bpdu("eth0", worse_bridge)
    proc.process_bpdu("eth1", better_bridge)
    assert proc.root_port == "eth1"

    better_port = BPDU(
        root_id=BridgeId(32768, "00:00:00:00:00:01"),
        root_path_cost=6,
        bridge_id=BridgeId(32768, "00:00:00:00:00:02"),
        port_id=10,
    )
    proc.process_bpdu("eth0", better_port)
    assert proc.root_port == "eth0"


def test_recompute_clears_stale_non_root_roles_when_becoming_root() -> None:
    proc = _make_proc(32768, "00:00:00:00:00:0a")
    proc.root_id = BridgeId(32768, "00:00:00:00:00:01")
    proc.root_port = "eth1"
    proc.recompute_port_states()
    assert proc.ports["eth0"].role == STPRole.ALTERNATE

    proc.root_id = proc.bridge_id
    proc.recompute_port_states()

    assert proc.root_port is None
    for port in proc.ports.values():
        assert port.role == STPRole.DESIGNATED
        assert port.state == STPState.FORWARDING


def test_unknown_ingress_interface_is_ignored() -> None:
    proc = _make_proc(32768, "00:00:00:00:00:0a")
    before = (proc.root_id, proc.root_cost, proc.root_port)

    bpdu = BPDU(
        root_id=BridgeId(32768, "00:00:00:00:00:01"),
        root_path_cost=1,
        bridge_id=BridgeId(32768, "00:00:00:00:00:01"),
        port_id=1,
    )
    proc.process_bpdu("eth999", bpdu)

    after = (proc.root_id, proc.root_cost, proc.root_port)
    assert after == before
