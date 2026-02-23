"""Edge-case tests for Lab 30 route selection and redistribution."""

from __future__ import annotations

import pytest

from pycie.protocols.route_selection import RouteCandidate, RouteProtocol, RouteSelectionEngine

pytestmark = [pytest.mark.exercise, pytest.mark.lab30]


def _r(prefix: str, nh: str, proto: RouteProtocol, ad: int, metric: int) -> RouteCandidate:
    return RouteCandidate(prefix=prefix, next_hop=nh, protocol=proto, admin_distance=ad, metric=metric)


def test_best_route_tie_breaks_on_next_hop_when_other_fields_equal() -> None:
    engine = RouteSelectionEngine()
    engine.install_route(_r("10.0.0.0/24", "192.0.2.20", RouteProtocol.OSPF, 110, 10))
    engine.install_route(_r("10.0.0.0/24", "192.0.2.10", RouteProtocol.OSPF, 110, 10))

    best = engine.best_route("10.0.0.9")
    assert best is not None
    assert best.next_hop == "192.0.2.10"


def test_withdraw_route_without_next_hop_removes_all_matching_protocol_routes() -> None:
    engine = RouteSelectionEngine()
    engine.install_route(_r("10.1.0.0/16", "192.0.2.1", RouteProtocol.OSPF, 110, 20))
    engine.install_route(_r("10.1.0.0/16", "192.0.2.2", RouteProtocol.OSPF, 110, 5))
    engine.install_route(_r("10.1.0.0/16", "192.0.2.3", RouteProtocol.BGP, 200, 1))

    engine.withdraw_route("10.1.0.0/16", RouteProtocol.OSPF)
    best = engine.best_route("10.1.9.9")
    assert best is not None
    assert best.protocol == RouteProtocol.BGP

