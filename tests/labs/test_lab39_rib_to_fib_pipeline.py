"""Exercise tests for Lab 39 RIB-to-FIB pipeline."""

from __future__ import annotations

import pytest

from pycie.protocols.rib_fib_pipeline import (
    NextHopResolution,
    PipelineRoute,
    RIBFIBPipeline,
)

pytestmark = [pytest.mark.exercise, pytest.mark.lab39]


def _route(prefix: str, nh: str, proto: str, ad: int, metric: int) -> PipelineRoute:
    return PipelineRoute(prefix=prefix, next_hop=nh, protocol=proto, admin_distance=ad, metric=metric)


def test_best_route_for_prefix_uses_ad_then_metric_then_protocol() -> None:
    p = RIBFIBPipeline()
    p.install_route(_route("10.0.0.0/24", "192.0.2.1", "ospf", 110, 20))
    p.install_route(_route("10.0.0.0/24", "192.0.2.2", "isis", 110, 10))

    best = p.best_route_for_prefix("10.0.0.0/24")
    assert best is not None
    assert best.next_hop == "192.0.2.2"


def test_recompute_installs_fib_when_next_hop_resolved() -> None:
    p = RIBFIBPipeline()
    p.install_route(_route("10.1.0.0/24", "192.0.2.1", "ospf", 110, 20))
    p.set_next_hop_resolution(NextHopResolution(next_hop="192.0.2.1", egress_if="eth0"))

    p.recompute()
    assert p.fib["10.1.0.0/24"].egress_if == "eth0"


def test_recompute_skips_unresolved_route_and_records_trace() -> None:
    p = RIBFIBPipeline()
    p.install_route(_route("10.2.0.0/24", "192.0.2.9", "ospf", 110, 20))

    p.recompute()
    assert "10.2.0.0/24" not in p.fib
    details = [step.detail for step in p.explain("10.2.0.0/24")]
    assert "unresolved_next_hop" in details


def test_recursive_next_hop_resolution_succeeds() -> None:
    p = RIBFIBPipeline()
    p.install_route(_route("10.3.0.0/24", "198.51.100.1", "ospf", 110, 20))
    p.set_next_hop_resolution(NextHopResolution(next_hop="198.51.100.1", egress_if="eth1", recursive_next_hop="192.0.2.1"))
    p.set_next_hop_resolution(NextHopResolution(next_hop="192.0.2.1", egress_if="eth2"))

    p.recompute()
    assert p.fib["10.3.0.0/24"].egress_if == "eth2"
    assert p.fib["10.3.0.0/24"].next_hop == "192.0.2.1"


def test_recursive_loop_detection_prevents_install() -> None:
    p = RIBFIBPipeline()
    p.install_route(_route("10.4.0.0/24", "192.0.2.1", "ospf", 110, 20))
    p.set_next_hop_resolution(NextHopResolution(next_hop="192.0.2.1", egress_if="eth0", recursive_next_hop="192.0.2.2"))
    p.set_next_hop_resolution(NextHopResolution(next_hop="192.0.2.2", egress_if="eth1", recursive_next_hop="192.0.2.1"))

    p.recompute()
    assert "10.4.0.0/24" not in p.fib


def test_lookup_uses_longest_prefix_match() -> None:
    p = RIBFIBPipeline()
    p.install_route(_route("10.0.0.0/8", "192.0.2.1", "ospf", 110, 20))
    p.install_route(_route("10.10.0.0/16", "192.0.2.2", "ospf", 110, 20))
    p.set_next_hop_resolution(NextHopResolution(next_hop="192.0.2.1", egress_if="eth0"))
    p.set_next_hop_resolution(NextHopResolution(next_hop="192.0.2.2", egress_if="eth1"))

    p.recompute()
    hit = p.lookup("10.10.1.1")
    assert hit is not None
    assert hit.prefix == "10.10.0.0/16"


def test_withdraw_route_and_recompute_removes_fib_entry() -> None:
    p = RIBFIBPipeline()
    p.install_route(_route("10.5.0.0/24", "192.0.2.1", "ospf", 110, 20))
    p.set_next_hop_resolution(NextHopResolution(next_hop="192.0.2.1", egress_if="eth0"))
    p.recompute()
    assert "10.5.0.0/24" in p.fib

    p.withdraw_route("10.5.0.0/24", "ospf")
    p.recompute()
    assert "10.5.0.0/24" not in p.fib


def test_explain_contains_selection_and_install_steps() -> None:
    p = RIBFIBPipeline()
    p.install_route(_route("10.6.0.0/24", "192.0.2.1", "ospf", 110, 20))
    p.set_next_hop_resolution(NextHopResolution(next_hop="192.0.2.1", egress_if="eth9"))

    p.recompute()
    steps = [step.step for step in p.explain("10.6.0.0/24")]
    assert "selected" in steps
    assert "installed" in steps
