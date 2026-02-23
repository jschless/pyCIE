"""Edge-case tests for Lab 03 OSPF."""

from __future__ import annotations

import pytest

from pycie.protocols.ospf import OSPFHello, OSPFProcess, RouterLSA

pytestmark = [pytest.mark.exercise, pytest.mark.lab03]


def _lsa(router: str, seq: int, links: tuple[tuple[str, int], ...]) -> RouterLSA:
    return RouterLSA(advertising_router=router, lsa_id=router, sequence=seq, links=links)


def test_hello_with_wrong_area_is_ignored() -> None:
    ospf = OSPFProcess(router_id="1.1.1.1", area_id=0)
    hello = OSPFHello(
        router_id="2.2.2.2",
        area_id=1,
        hello_interval_ms=10_000,
        dead_interval_ms=40_000,
        neighbors=("1.1.1.1",),
    )

    ospf.process_hello("eth0", hello)
    assert "2.2.2.2" not in ospf.neighbors


def test_spf_returns_self_only_when_no_local_lsa() -> None:
    ospf = OSPFProcess(router_id="1.1.1.1")
    ospf.lsdb = {"2.2.2.2": _lsa("2.2.2.2", 1, ())}

    assert ospf.run_spf() == {"1.1.1.1": (0, None)}
