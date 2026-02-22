"""Exercise tests for Lab 04 BGP."""

from __future__ import annotations

import pytest

from pycie.protocols.bgp import BGPPeer, BGPProcess, BGPUpdate

pytestmark = [pytest.mark.exercise, pytest.mark.lab04]


def _u(prefix: str, nh: str, as_path: tuple[int, ...], local_pref: int, med: int = 0) -> BGPUpdate:
    return BGPUpdate(prefix=prefix, next_hop=nh, as_path=as_path, local_pref=local_pref, med=med)


def test_process_update_stores_candidate_by_peer() -> None:
    bgp = BGPProcess(local_as=65001, router_id="1.1.1.1")
    bgp.peers["2.2.2.2"] = BGPPeer("2.2.2.2", 65002, is_ibgp=False)

    update = _u("10.10.10.0/24", "192.0.2.2", (65002,), 100)
    bgp.process_update("2.2.2.2", update)

    assert "2.2.2.2" in bgp.adj_rib_in
    assert bgp.adj_rib_in["2.2.2.2"][0] == update


def test_best_path_prefers_higher_local_pref_then_shorter_as_path() -> None:
    bgp = BGPProcess(local_as=65001, router_id="1.1.1.1")
    bgp.adj_rib_in = {
        "2.2.2.2": [_u("10.0.0.0/24", "192.0.2.2", (65002,), 200)],
        "3.3.3.3": [_u("10.0.0.0/24", "192.0.2.3", (65003, 64496), 100)],
    }

    best = bgp.best_path("10.0.0.0/24")
    assert best is not None
    assert best.next_hop == "192.0.2.2"


def test_recompute_loc_rib_keeps_one_best_route_per_prefix() -> None:
    bgp = BGPProcess(local_as=65001, router_id="1.1.1.1")
    bgp.adj_rib_in = {
        "2.2.2.2": [_u("10.0.0.0/24", "192.0.2.2", (65002,), 100)],
        "3.3.3.3": [_u("10.0.0.0/24", "192.0.2.3", (65003,), 150)],
        "4.4.4.4": [_u("10.1.0.0/24", "192.0.2.4", (65004,), 120)],
    }

    bgp.recompute_loc_rib()
    assert set(bgp.loc_rib) == {"10.0.0.0/24", "10.1.0.0/24"}
    assert bgp.loc_rib["10.0.0.0/24"].next_hop == "192.0.2.3"


def test_export_updates_for_peer_filters_as_needed() -> None:
    bgp = BGPProcess(local_as=65001, router_id="1.1.1.1")
    bgp.loc_rib = {
        "10.0.0.0/24": _u("10.0.0.0/24", "192.0.2.2", (65002,), 100),
        "10.1.0.0/24": _u("10.1.0.0/24", "192.0.2.3", (65003,), 100),
    }
    bgp.peers["2.2.2.2"] = BGPPeer("2.2.2.2", 65002, is_ibgp=False)

    out = bgp.export_updates_for_peer("2.2.2.2")
    assert all(isinstance(u, BGPUpdate) for u in out)
