"""Edge-case tests for Lab 38 control-plane databases."""

from __future__ import annotations

import pytest

from pycie.protocols.control_plane_db import BGPDatabase, BGPPath, LDPDatabase

pytestmark = [pytest.mark.exercise, pytest.mark.lab38]


def test_bgp_withdrawing_last_candidate_removes_loc_rib_prefix() -> None:
    db = BGPDatabase()
    path = BGPPath("10.0.0.0/24", "192.0.2.2", (65002,), 100, 10, "peer-a", 10)
    db.install_path(path)
    assert "10.0.0.0/24" in db.loc_rib

    db.withdraw_path("peer-a", "10.0.0.0/24")
    assert "10.0.0.0/24" not in db.loc_rib


def test_ldp_best_binding_returns_none_when_fec_unknown() -> None:
    db = LDPDatabase()
    assert db.best_binding("203.0.113.0/24") is None

