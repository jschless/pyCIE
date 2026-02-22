"""Exercise tests for Lab 23 IS-IS."""

from __future__ import annotations

import pytest

from pycie.protocols.isis import ISISLSP, ISISNeighbor, ISISProcess
from pycie.sim.network import Frame

pytestmark = [pytest.mark.exercise, pytest.mark.lab23]


def _proc(system_id: str = "0000.0000.0001") -> ISISProcess:
    return ISISProcess(system_id=system_id)


def test_install_lsp_accepts_only_newer_sequence() -> None:
    p = _proc()
    base = ISISLSP(system_id="0000.0000.0002", level=1, sequence=10, links=())
    older = ISISLSP(system_id="0000.0000.0002", level=1, sequence=9, links=())

    assert p.install_lsp(base)
    assert not p.install_lsp(older)
    assert p.lsdb[(1, "0000.0000.0002")].sequence == 10


def test_originate_lsp_increments_sequence_after_install() -> None:
    p = _proc()
    p.set_neighbor(ISISNeighbor(system_id="0000.0000.0002", metric=5, levels=(1,)))

    first = p.originate_lsp(1)
    p.install_lsp(first)
    second = p.originate_lsp(1)

    assert first.sequence == 1
    assert second.sequence == 2
    assert second.links == (("0000.0000.0002", 5),)


def test_run_spf_prefers_lower_total_cost_path() -> None:
    p = _proc()
    p.install_lsp(ISISLSP(system_id="0000.0000.0001", level=1, sequence=1, links=(("0000.0000.0002", 5), ("0000.0000.0003", 20))))
    p.install_lsp(ISISLSP(system_id="0000.0000.0002", level=1, sequence=1, links=(("0000.0000.0004", 5),)))
    p.install_lsp(ISISLSP(system_id="0000.0000.0003", level=1, sequence=1, links=(("0000.0000.0004", 1),)))

    spf = p.run_spf(1)
    assert spf["0000.0000.0004"] == (10, "0000.0000.0002")


def test_run_spf_tie_breaks_on_next_hop_id() -> None:
    p = _proc()
    p.install_lsp(ISISLSP(system_id="0000.0000.0001", level=1, sequence=1, links=(("0000.0000.0002", 10), ("0000.0000.0003", 10))))
    p.install_lsp(ISISLSP(system_id="0000.0000.0002", level=1, sequence=1, links=(("0000.0000.0004", 5),)))
    p.install_lsp(ISISLSP(system_id="0000.0000.0003", level=1, sequence=1, links=(("0000.0000.0004", 5),)))

    spf = p.run_spf(1)
    assert spf["0000.0000.0004"] == (15, "0000.0000.0002")


def test_overloaded_router_is_not_used_as_transit() -> None:
    p = _proc()
    p.install_lsp(ISISLSP(system_id="0000.0000.0001", level=1, sequence=1, links=(("0000.0000.0002", 1), ("0000.0000.0003", 10))))
    p.install_lsp(ISISLSP(system_id="0000.0000.0002", level=1, sequence=1, links=(("0000.0000.0004", 1),), overload=True))
    p.install_lsp(ISISLSP(system_id="0000.0000.0003", level=1, sequence=1, links=(("0000.0000.0004", 1),)))

    spf = p.run_spf(1)
    assert spf["0000.0000.0004"] == (11, "0000.0000.0003")


def test_compute_routing_table_prefers_level1_when_available() -> None:
    p = _proc()
    p.install_lsp(ISISLSP(system_id="0000.0000.0001", level=1, sequence=1, links=(("0000.0000.0009", 5),)))
    p.install_lsp(ISISLSP(system_id="0000.0000.0001", level=2, sequence=1, links=(("0000.0000.0009", 1),)))

    table = p.compute_routing_table()
    assert table["0000.0000.0009"] == (5, "0000.0000.0009", 1)


def test_on_frame_dispatches_lsp_payload() -> None:
    p = _proc()
    lsp = ISISLSP(system_id="0000.0000.0002", level=2, sequence=7, links=())
    frame = Frame(src_mac="aa", dst_mac="bb", ethertype="0x0000", payload=lsp)

    p.on_frame("eth0", frame)
    assert p.lsdb[(2, "0000.0000.0002")].sequence == 7


def test_run_spf_without_local_lsp_returns_self_only() -> None:
    p = _proc()
    assert p.run_spf(1) == {"0000.0000.0001": (0, None)}
