"""Edge-case tests for Lab 18 OSPF multi-area ABR behavior."""

from __future__ import annotations

import pytest

from pycie.protocols.ospf_multi_area import AreaPrefixLSA, OSPFMultiAreaProcess, OSPFRoute, SummaryLSA
from pycie.sim.network import Frame

pytestmark = [pytest.mark.exercise, pytest.mark.lab18]


def test_non_abr_does_not_originate_summaries() -> None:
    proc = OSPFMultiAreaProcess(router_id="1.1.1.1", attached_areas={0})
    proc.install_area_lsa(AreaPrefixLSA(advertising_router="1.1.1.1", area_id=0, prefix="10.0.0.0/24", cost=1))

    assert proc.run_abr() == []


def test_originate_summaries_skips_prefix_already_local_to_target_area() -> None:
    proc = OSPFMultiAreaProcess(router_id="1.1.1.1", attached_areas={0, 10})
    proc.install_area_lsa(AreaPrefixLSA(advertising_router="10.10.10.10", area_id=10, prefix="203.0.113.0/24", cost=10))
    proc.install_area_lsa(AreaPrefixLSA(advertising_router="0.0.0.9", area_id=0, prefix="203.0.113.0/24", cost=5))

    generated = proc.originate_summaries_for_target(10)
    assert all(lsa.prefix != "203.0.113.0/24" for lsa in generated)


def test_compute_routing_table_uses_inter_when_no_intra_exists() -> None:
    proc = OSPFMultiAreaProcess(router_id="1.1.1.1", attached_areas={0, 10})
    proc.install_summary_lsa(
        SummaryLSA(
            advertising_router="9.9.9.9",
            from_area=0,
            to_area=10,
            prefix="198.51.100.0/24",
            cost=15,
            sequence=1,
        )
    )

    table = proc.compute_routing_table(10)
    route: OSPFRoute = table["198.51.100.0/24"]
    assert route.route_type == "inter"
    assert route.source_area == 0


def test_install_summary_same_sequence_does_not_replace_existing() -> None:
    proc = OSPFMultiAreaProcess(router_id="1.1.1.1", attached_areas={0, 10})
    first = SummaryLSA(
        advertising_router="9.9.9.9",
        from_area=0,
        to_area=10,
        prefix="10.20.0.0/16",
        cost=22,
        sequence=4,
    )
    same_seq = SummaryLSA(
        advertising_router="9.9.9.9",
        from_area=0,
        to_area=10,
        prefix="10.20.0.0/16",
        cost=3,
        sequence=4,
    )

    assert proc.install_summary_lsa(first)
    assert not proc.install_summary_lsa(same_seq)
    assert proc.summary_lsdb[10][("9.9.9.9", "10.20.0.0/16", 0)].cost == 22


def test_on_frame_dispatches_area_and_summary_lsa_payloads() -> None:
    proc = OSPFMultiAreaProcess(router_id="1.1.1.1", attached_areas={0, 10})

    area_lsa = AreaPrefixLSA(advertising_router="10.10.10.10", area_id=10, prefix="10.10.0.0/16", cost=7, sequence=1)
    summary_lsa = SummaryLSA(
        advertising_router="2.2.2.2",
        from_area=0,
        to_area=10,
        prefix="172.16.0.0/16",
        cost=11,
        sequence=1,
    )
    proc.on_frame("eth0", Frame(src_mac="aa", dst_mac="bb", ethertype="0x0000", payload=area_lsa))
    proc.on_frame("eth1", Frame(src_mac="cc", dst_mac="dd", ethertype="0x0000", payload=summary_lsa))

    assert ("10.10.10.10", "10.10.0.0/16") in proc.area_lsdb[10]
    assert ("2.2.2.2", "172.16.0.0/16", 0) in proc.summary_lsdb[10]
