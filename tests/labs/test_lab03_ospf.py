"""Exercise tests for Lab 03 OSPF."""

from __future__ import annotations

import pytest

from pycie.protocols.ospf import OSPFHello, OSPFProcess, RouterLSA

pytestmark = [pytest.mark.exercise, pytest.mark.lab03]


def _lsa(router: str, seq: int, links: tuple[tuple[str, int], ...]) -> RouterLSA:
    return RouterLSA(
        advertising_router=router,
        lsa_id=router,
        sequence=seq,
        links=links,
    )


def test_install_lsa_accepts_newer_sequence() -> None:
    ospf = OSPFProcess(router_id="1.1.1.1")
    old = _lsa("2.2.2.2", 1, (("1.1.1.1", 10),))
    new = _lsa("2.2.2.2", 2, (("1.1.1.1", 5),))

    assert ospf.install_lsa(old)
    assert not ospf.install_lsa(old)
    assert ospf.install_lsa(new)


def test_process_hello_creates_or_updates_neighbor_state() -> None:
    ospf = OSPFProcess(router_id="1.1.1.1")
    hello = OSPFHello(
        router_id="2.2.2.2",
        area_id=0,
        hello_interval_ms=10_000,
        dead_interval_ms=40_000,
        neighbors=("1.1.1.1",),
    )

    ospf.process_hello("eth0", hello)
    assert "2.2.2.2" in ospf.neighbors
    assert ospf.neighbors["2.2.2.2"].state in {"INIT", "2WAY", "FULL"}


def test_run_spf_prefers_lower_path_cost() -> None:
    ospf = OSPFProcess(router_id="1.1.1.1")
    ospf.lsdb = {
        "1.1.1.1": _lsa("1.1.1.1", 1, (("2.2.2.2", 10), ("3.3.3.3", 100))),
        "2.2.2.2": _lsa("2.2.2.2", 1, (("3.3.3.3", 10),)),
        "3.3.3.3": _lsa("3.3.3.3", 1, ()),
    }

    spf = ospf.run_spf()
    assert spf["3.3.3.3"][0] == 20


def test_compute_routing_table_maps_destination_to_next_hop() -> None:
    ospf = OSPFProcess(router_id="1.1.1.1")
    ospf.lsdb = {
        "1.1.1.1": _lsa("1.1.1.1", 1, (("2.2.2.2", 10),)),
        "2.2.2.2": _lsa("2.2.2.2", 1, (("4.4.4.4", 5),)),
        "4.4.4.4": _lsa("4.4.4.4", 1, ()),
    }

    table = ospf.compute_routing_table()
    assert table["4.4.4.4"] == "2.2.2.2"
