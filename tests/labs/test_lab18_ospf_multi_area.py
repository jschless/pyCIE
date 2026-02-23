"""Exercise tests for Lab 18 OSPF multi-area ABR behavior."""

from __future__ import annotations

import pytest

from pycie.protocols.ospf_multi_area import AreaPrefixLSA, OSPFMultiAreaProcess, SummaryLSA

pytestmark = [pytest.mark.exercise, pytest.mark.lab18]


def _abr() -> OSPFMultiAreaProcess:
    return OSPFMultiAreaProcess(router_id="1.1.1.1", attached_areas={0, 10})


def test_run_abr_originates_summaries_between_backbone_and_non_backbone() -> None:
    proc = _abr()
    proc.install_area_lsa(AreaPrefixLSA(advertising_router="10.10.10.10", area_id=10, prefix="10.10.0.0/16", cost=20))

    generated = proc.run_abr()
    assert generated
    prefixes = {(lsa.from_area, lsa.to_area, lsa.prefix) for lsa in generated}
    assert (10, 0, "10.10.0.0/16") in prefixes
    assert proc.summary_lsdb[0][("1.1.1.1", "10.10.0.0/16", 10)].cost == 21


def test_non_backbone_areas_are_isolated_without_area_zero_transit() -> None:
    proc = OSPFMultiAreaProcess(router_id="2.2.2.2", attached_areas={10, 20})
    proc.install_area_lsa(AreaPrefixLSA(advertising_router="10.10.10.10", area_id=10, prefix="10.10.0.0/16", cost=10))
    proc.install_area_lsa(AreaPrefixLSA(advertising_router="20.20.20.20", area_id=20, prefix="20.20.0.0/16", cost=10))

    generated = proc.run_abr()
    assert generated == []
    table20 = proc.compute_routing_table(20)
    assert "10.10.0.0/16" not in table20


def test_routing_table_prefers_intra_area_over_summary_for_same_prefix() -> None:
    proc = _abr()
    proc.install_area_lsa(AreaPrefixLSA(advertising_router="10.10.10.10", area_id=10, prefix="192.0.2.0/24", cost=5))
    proc.install_summary_lsa(
        SummaryLSA(
            advertising_router="9.9.9.9",
            from_area=0,
            to_area=10,
            prefix="192.0.2.0/24",
            cost=2,
            sequence=1,
        )
    )

    table = proc.compute_routing_table(10)
    assert table["192.0.2.0/24"].route_type == "intra"
    assert table["192.0.2.0/24"].next_hop == "10.10.10.10"


def test_summary_tie_break_prefers_lower_advertising_router_id() -> None:
    proc = _abr()
    proc.install_summary_lsa(
        SummaryLSA(
            advertising_router="9.9.9.9",
            from_area=0,
            to_area=10,
            prefix="198.51.100.0/24",
            cost=20,
            sequence=1,
        )
    )
    proc.install_summary_lsa(
        SummaryLSA(
            advertising_router="8.8.8.8",
            from_area=0,
            to_area=10,
            prefix="198.51.100.0/24",
            cost=20,
            sequence=1,
        )
    )

    table = proc.compute_routing_table(10)
    assert table["198.51.100.0/24"].route_type == "inter"
    assert table["198.51.100.0/24"].next_hop == "8.8.8.8"


def test_install_lsa_accepts_only_newer_sequence() -> None:
    proc = _abr()
    newer = AreaPrefixLSA(advertising_router="10.10.10.10", area_id=10, prefix="10.10.0.0/16", cost=10, sequence=7)
    older = AreaPrefixLSA(advertising_router="10.10.10.10", area_id=10, prefix="10.10.0.0/16", cost=2, sequence=6)

    assert proc.install_area_lsa(newer)
    assert not proc.install_area_lsa(older)
    assert proc.area_lsdb[10][("10.10.10.10", "10.10.0.0/16")].cost == 10
