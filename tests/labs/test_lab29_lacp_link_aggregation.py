"""Exercise tests for Lab 29 LACP link aggregation."""

from __future__ import annotations

import pytest

from pycie.protocols.lacp import LACPProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab29]


def test_receive_lacpdu_with_matching_key_activates_members() -> None:
    proc = LACPProcess(system_id="00:00:00:00:00:01", admin_key=100)
    proc.add_port("eth0")
    proc.add_port("eth1")
    proc.receive_lacpdu("eth0", partner_system="00:00:00:00:00:aa", partner_key=100, now_ms=100)
    proc.receive_lacpdu("eth1", partner_system="00:00:00:00:00:aa", partner_key=100, now_ms=100)

    assert proc.active_members() == ["eth0", "eth1"]


def test_mismatched_partner_key_prevents_bundle_membership() -> None:
    proc = LACPProcess(system_id="00:00:00:00:00:01", admin_key=100)
    proc.add_port("eth0")
    proc.receive_lacpdu("eth0", partner_system="00:00:00:00:00:aa", partner_key=200, now_ms=100)

    assert proc.active_members() == []


def test_select_egress_is_deterministic_by_hash() -> None:
    proc = LACPProcess(system_id="00:00:00:00:00:01", admin_key=100)
    proc.add_port("eth0")
    proc.add_port("eth1")
    proc.receive_lacpdu("eth0", partner_system="00:00:00:00:00:aa", partner_key=100, now_ms=100)
    proc.receive_lacpdu("eth1", partner_system="00:00:00:00:00:aa", partner_key=100, now_ms=100)

    assert proc.select_egress(0) == "eth0"
    assert proc.select_egress(1) == "eth1"
    assert proc.select_egress(2) == "eth0"


def test_port_down_removes_member_from_selection() -> None:
    proc = LACPProcess(system_id="00:00:00:00:00:01", admin_key=100)
    proc.add_port("eth0")
    proc.add_port("eth1")
    proc.receive_lacpdu("eth0", partner_system="00:00:00:00:00:aa", partner_key=100, now_ms=100)
    proc.receive_lacpdu("eth1", partner_system="00:00:00:00:00:aa", partner_key=100, now_ms=100)

    proc.set_port_up("eth1", up=False)
    assert proc.active_members() == ["eth0"]
    assert proc.select_egress(99) == "eth0"
