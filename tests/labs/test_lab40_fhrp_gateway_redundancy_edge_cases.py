"""Edge-case tests for Lab 40 first-hop redundancy."""

from __future__ import annotations

import pytest

from pycie.protocols.fhrp import FHRPProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab40]


def test_elect_master_returns_none_with_no_members() -> None:
    proc = FHRPProcess()
    assert proc.elect_master() is None


def test_update_unknown_router_raises() -> None:
    proc = FHRPProcess()
    with pytest.raises(ValueError, match="unknown_router"):
        proc.update_router("r9", up=False)


def test_non_preempting_router_does_not_take_over() -> None:
    proc = FHRPProcess(group_id=1)
    proc.register_router("r1", priority=100, preempt=True)
    proc.register_router("r2", priority=90, preempt=False)
    assert proc.master_id == "r1"

    proc.update_router("r2", priority=150, preempt=False, now_ms=100)
    assert proc.master_id == "r1"


def test_tie_break_prefers_lexicographically_lower_router_id() -> None:
    proc = FHRPProcess(group_id=1)
    proc.register_router("r2", priority=100)
    proc.register_router("r1", priority=100)

    assert proc.master_id == "r1"
