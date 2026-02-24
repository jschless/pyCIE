"""Exercise tests for Lab 40 first-hop redundancy."""

from __future__ import annotations

import pytest

from pycie.protocols.fhrp import FHRPProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab40]


def test_register_router_elects_highest_priority_master() -> None:
    proc = FHRPProcess(group_id=1)
    proc.register_router("r1", priority=100)
    proc.register_router("r2", priority=120)

    assert proc.master_id == "r2"


def test_master_failover_when_current_master_goes_down() -> None:
    proc = FHRPProcess(group_id=1)
    proc.register_router("r1", priority=100)
    proc.register_router("r2", priority=120)

    proc.update_router("r2", up=False, now_ms=1_000)
    assert proc.master_id == "r1"
    assert proc.failover_elapsed_ms(now_ms=1_050) == 50


def test_higher_priority_router_preempts_when_enabled() -> None:
    proc = FHRPProcess(group_id=1)
    proc.register_router("r1", priority=100, preempt=True)
    proc.register_router("r2", priority=90, preempt=True)
    assert proc.master_id == "r1"

    proc.update_router("r2", priority=150, preempt=True, now_ms=100)
    assert proc.master_id == "r2"


def test_virtual_mac_is_deterministic_from_group_id() -> None:
    proc = FHRPProcess(group_id=10)
    assert proc.current_virtual_mac() == "00:00:5e:00:01:0a"
