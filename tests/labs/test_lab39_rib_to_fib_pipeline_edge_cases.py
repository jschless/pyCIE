"""Edge-case tests for Lab 39 RIB-to-FIB pipeline."""

from __future__ import annotations

import pytest

from pycie.protocols.rib_fib_pipeline import NextHopResolution, PipelineRoute, RIBFIBPipeline

pytestmark = [pytest.mark.exercise, pytest.mark.lab39]


def test_resolve_next_hop_returns_none_when_recursion_depth_exceeded() -> None:
    p = RIBFIBPipeline()
    p.set_next_hop_resolution(NextHopResolution(next_hop="192.0.2.1", egress_if="eth0", recursive_next_hop="192.0.2.2"))
    p.set_next_hop_resolution(NextHopResolution(next_hop="192.0.2.2", egress_if="eth1", recursive_next_hop="192.0.2.3"))
    p.set_next_hop_resolution(NextHopResolution(next_hop="192.0.2.3", egress_if="eth2"))

    assert p.resolve_next_hop("192.0.2.1", max_depth=1) is None


def test_explain_returns_empty_for_prefix_without_trace() -> None:
    p = RIBFIBPipeline()
    assert p.explain("10.255.255.0/24") == []


def test_recompute_falls_back_to_resolvable_alternate_candidate() -> None:
    p = RIBFIBPipeline()
    p.install_route(PipelineRoute("10.9.0.0/24", "192.0.2.1", "static", 1, 0))
    p.install_route(PipelineRoute("10.9.0.0/24", "192.0.2.2", "ospf", 110, 20))
    p.set_next_hop_resolution(NextHopResolution(next_hop="192.0.2.2", egress_if="eth7"))

    p.recompute()

    assert p.fib["10.9.0.0/24"].egress_if == "eth7"
    assert p.fib["10.9.0.0/24"].source_protocol == "ospf"
    steps = [step.step for step in p.explain("10.9.0.0/24")]
    assert "candidate_unresolved" in steps
    assert "selected" in steps
