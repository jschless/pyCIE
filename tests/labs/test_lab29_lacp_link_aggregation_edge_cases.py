"""Edge-case tests for Lab 29 LACP link aggregation."""

from __future__ import annotations

import pytest

from pycie.protocols.lacp import LACPProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab29]


def test_age_sessions_expires_synchronization() -> None:
    proc = LACPProcess(admin_key=10)
    proc.add_port("eth0")
    proc.receive_lacpdu("eth0", partner_system="00:00:00:00:00:aa", partner_key=10, now_ms=100)
    assert proc.active_members() == ["eth0"]

    proc.age_sessions(now_ms=200_000, timeout_ms=1_000)
    assert proc.active_members() == []


def test_select_egress_returns_none_when_no_active_members() -> None:
    proc = LACPProcess()
    assert proc.select_egress(0) is None


def test_receive_lacpdu_on_unknown_port_creates_port() -> None:
    proc = LACPProcess(admin_key=5)
    proc.receive_lacpdu("eth9", partner_system="00:00:00:00:00:aa", partner_key=5, now_ms=10)

    assert "eth9" in proc.ports
    assert proc.active_members() == ["eth9"]


def test_active_members_sort_by_priority_then_name() -> None:
    proc = LACPProcess(admin_key=5)
    proc.add_port("eth1", port_priority=200)
    proc.add_port("eth0", port_priority=100)
    proc.receive_lacpdu("eth0", partner_system="00:00:00:00:00:aa", partner_key=5, now_ms=10)
    proc.receive_lacpdu("eth1", partner_system="00:00:00:00:00:aa", partner_key=5, now_ms=10)

    assert proc.active_members() == ["eth0", "eth1"]
