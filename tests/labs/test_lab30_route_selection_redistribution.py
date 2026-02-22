"""Exercise tests for Lab 30 route selection and redistribution."""

from __future__ import annotations

import pytest

from pycie.protocols.route_selection import RouteCandidate, RouteProtocol, RouteSelectionEngine

pytestmark = [pytest.mark.exercise, pytest.mark.lab30]


def _r(prefix: str, nh: str, proto: RouteProtocol, ad: int, metric: int, tags: set[str] | None = None) -> RouteCandidate:
    return RouteCandidate(prefix=prefix, next_hop=nh, protocol=proto, admin_distance=ad, metric=metric, tags=frozenset(tags or set()))


def test_best_route_respects_lpm_before_admin_distance() -> None:
    engine = RouteSelectionEngine()
    engine.install_route(_r("10.0.0.0/8", "192.0.2.1", RouteProtocol.CONNECTED, 0, 1))
    engine.install_route(_r("10.1.0.0/16", "192.0.2.200", RouteProtocol.BGP, 200, 50))

    best = engine.best_route("10.1.2.3")
    assert best is not None
    assert best.prefix == "10.1.0.0/16"


def test_best_route_tie_breaks_on_ad_then_metric_then_protocol() -> None:
    engine = RouteSelectionEngine()
    engine.install_route(_r("203.0.113.0/24", "192.0.2.5", RouteProtocol.OSPF, 110, 20))
    engine.install_route(_r("203.0.113.0/24", "192.0.2.6", RouteProtocol.ISIS, 110, 5))
    engine.install_route(_r("203.0.113.0/24", "192.0.2.7", RouteProtocol.BGP, 200, 1))

    best = engine.best_route("203.0.113.77")
    assert best is not None
    assert best.next_hop == "192.0.2.6"


def test_explain_returns_ranked_candidates() -> None:
    engine = RouteSelectionEngine()
    engine.install_route(_r("198.51.100.0/24", "192.0.2.10", RouteProtocol.OSPF, 110, 20))
    engine.install_route(_r("198.51.100.0/24", "192.0.2.11", RouteProtocol.OSPF, 110, 5))

    trace = engine.explain("198.51.100.99")
    assert trace.reason == "lpm_ad_metric_protocol_next_hop"
    assert trace.selected is not None
    assert trace.selected.next_hop == "192.0.2.11"
    assert len(trace.candidates) == 2


def test_withdraw_route_can_target_single_next_hop() -> None:
    engine = RouteSelectionEngine()
    engine.install_route(_r("10.20.0.0/16", "192.0.2.1", RouteProtocol.OSPF, 110, 10))
    engine.install_route(_r("10.20.0.0/16", "192.0.2.2", RouteProtocol.OSPF, 110, 20))

    engine.withdraw_route("10.20.0.0/16", RouteProtocol.OSPF, next_hop="192.0.2.1")
    best = engine.best_route("10.20.1.1")
    assert best is not None
    assert best.next_hop == "192.0.2.2"


def test_redistribute_adds_tag_and_metric_increment() -> None:
    engine = RouteSelectionEngine()
    engine.install_route(_r("172.16.0.0/16", "192.0.2.9", RouteProtocol.OSPF, 110, 25))

    exported = engine.redistribute(RouteProtocol.OSPF, RouteProtocol.BGP, route_tag="from-ospf", metric_increment=7)
    assert len(exported) == 1
    assert exported[0].protocol == RouteProtocol.BGP
    assert exported[0].metric == 32
    assert "from-ospf" in exported[0].tags


def test_redistribute_skips_pretagged_candidates_to_prevent_loops() -> None:
    engine = RouteSelectionEngine()
    engine.install_route(_r("172.17.0.0/16", "192.0.2.9", RouteProtocol.OSPF, 110, 25, tags={"from-ospf"}))

    exported = engine.redistribute(RouteProtocol.OSPF, RouteProtocol.BGP, route_tag="from-ospf")
    assert exported == []


def test_redistribute_skips_same_protocol() -> None:
    engine = RouteSelectionEngine()
    engine.install_route(_r("172.18.0.0/16", "192.0.2.9", RouteProtocol.OSPF, 110, 25))

    exported = engine.redistribute(RouteProtocol.OSPF, RouteProtocol.OSPF, route_tag="loop")
    assert exported == []


def test_best_route_returns_none_when_no_match() -> None:
    engine = RouteSelectionEngine()
    engine.install_route(_r("192.0.2.0/24", "192.0.2.1", RouteProtocol.CONNECTED, 0, 0))
    assert engine.best_route("203.0.113.1") is None
