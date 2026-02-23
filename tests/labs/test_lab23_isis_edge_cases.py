"""Edge-case tests for Lab 23 IS-IS."""

from __future__ import annotations

import pytest

from pycie.protocols.isis import ISISLSP, ISISProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab23]


def test_install_lsp_same_sequence_does_not_replace_existing_state() -> None:
    proc = ISISProcess(system_id="0000.0000.0001")
    first = ISISLSP(system_id="0000.0000.0002", level=1, sequence=10, links=(("0000.0000.0003", 5),))
    same_seq = ISISLSP(system_id="0000.0000.0002", level=1, sequence=10, links=(("0000.0000.0004", 9),))

    assert proc.install_lsp(first)
    assert not proc.install_lsp(same_seq)
    assert proc.lsdb[(1, "0000.0000.0002")].links == (("0000.0000.0003", 5),)


def test_compute_routing_table_uses_level2_when_level1_disabled() -> None:
    proc = ISISProcess(system_id="0000.0000.0001", level1_enabled=False, level2_enabled=True)
    proc.install_lsp(ISISLSP(system_id="0000.0000.0001", level=2, sequence=1, links=(("0000.0000.0009", 7),)))
    proc.install_lsp(ISISLSP(system_id="0000.0000.0009", level=2, sequence=1, links=()))

    table = proc.compute_routing_table()
    assert table["0000.0000.0009"] == (7, "0000.0000.0009", 2)

