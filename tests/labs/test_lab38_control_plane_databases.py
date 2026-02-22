"""Exercise tests for Lab 38 control-plane databases."""

from __future__ import annotations

import pytest

from pycie.protocols.control_plane_db import (
    BGPDatabase,
    BGPPath,
    LDPBinding,
    LDPDatabase,
    OSPFLSA,
    OSPFLSDB,
)

pytestmark = [pytest.mark.exercise, pytest.mark.lab38]


def test_ospf_lsdb_accepts_only_newer_sequence() -> None:
    db = OSPFLSDB()
    new = OSPFLSA("1.1.1.1", "1.1.1.1", 10, (), 100)
    old = OSPFLSA("1.1.1.1", "1.1.1.1", 9, (), 101)

    assert db.install(new)
    assert not db.install(old)
    assert db.records[("1.1.1.1", "1.1.1.1")].sequence == 10


def test_ospf_withdraw_removes_record() -> None:
    db = OSPFLSDB()
    db.install(OSPFLSA("1.1.1.1", "1.1.1.1", 1, (), 0))

    db.withdraw("1.1.1.1", "1.1.1.1")
    assert db.records == {}


def test_bgp_database_best_path_selection() -> None:
    db = BGPDatabase()
    db.install_path(BGPPath("10.0.0.0/24", "192.0.2.2", (65002,), 100, 50, "peer-a", 10))
    db.install_path(BGPPath("10.0.0.0/24", "192.0.2.3", (65003, 64496), 200, 0, "peer-b", 10))

    best = db.loc_rib.get("10.0.0.0/24")
    assert best is not None
    assert best.next_hop == "192.0.2.3"


def test_bgp_older_timestamp_does_not_replace_peer_path() -> None:
    db = BGPDatabase()
    db.install_path(BGPPath("10.1.0.0/24", "192.0.2.2", (65002,), 100, 10, "peer-a", 20))
    db.install_path(BGPPath("10.1.0.0/24", "192.0.2.9", (65002,), 100, 5, "peer-a", 10))

    assert db.adj_rib_in["peer-a"]["10.1.0.0/24"].next_hop == "192.0.2.2"


def test_bgp_withdraw_recomputes_loc_rib() -> None:
    db = BGPDatabase()
    a = BGPPath("10.2.0.0/24", "192.0.2.2", (65002,), 100, 10, "peer-a", 20)
    b = BGPPath("10.2.0.0/24", "192.0.2.3", (65003,), 100, 20, "peer-b", 20)
    db.install_path(a)
    db.install_path(b)

    db.withdraw_path("peer-a", "10.2.0.0/24")
    assert db.loc_rib["10.2.0.0/24"].next_hop == "192.0.2.3"


def test_ldp_best_binding_prefers_lowest_label_then_peer() -> None:
    db = LDPDatabase()
    db.install_binding(LDPBinding("10.0.0.0/24", 300, "peer-b", 10))
    db.install_binding(LDPBinding("10.0.0.0/24", 200, "peer-a", 10))

    best = db.best_binding("10.0.0.0/24")
    assert best is not None
    assert best.label == 200
    assert best.peer == "peer-a"


def test_ldp_older_binding_update_is_ignored() -> None:
    db = LDPDatabase()
    db.install_binding(LDPBinding("10.0.1.0/24", 400, "peer-a", 20))
    db.install_binding(LDPBinding("10.0.1.0/24", 300, "peer-a", 10))

    bindings = db.bindings_for_fec("10.0.1.0/24")
    assert bindings[0].label == 400


def test_ldp_withdraw_removes_only_target_binding() -> None:
    db = LDPDatabase()
    db.install_binding(LDPBinding("10.0.2.0/24", 500, "peer-a", 10))
    db.install_binding(LDPBinding("10.0.2.0/24", 600, "peer-b", 10))

    db.withdraw_binding("peer-a", "10.0.2.0/24")
    remaining = db.bindings_for_fec("10.0.2.0/24")
    assert len(remaining) == 1
    assert remaining[0].peer == "peer-b"
