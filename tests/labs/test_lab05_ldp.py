"""Exercise tests for Lab 05 LDP."""

from __future__ import annotations

import pytest

from pycie.protocols.ldp import LDPProcess, LabelMapping

pytestmark = [pytest.mark.exercise, pytest.mark.lab05]


def test_allocate_local_label_is_stable_for_prefix() -> None:
    ldp = LDPProcess(router_id="1.1.1.1")

    a = ldp.allocate_local_label("10.0.0.0/24")
    b = ldp.allocate_local_label("10.0.0.0/24")
    c = ldp.allocate_local_label("10.1.0.0/24")

    assert a == b
    assert c != a
    assert a >= 16 and c >= 16


def test_process_label_mapping_stores_remote_binding() -> None:
    ldp = LDPProcess(router_id="1.1.1.1")
    mapping = LabelMapping(prefix="10.0.0.0/24", label=16000, next_hop="2.2.2.2")

    ldp.process_label_mapping("2.2.2.2", mapping)

    assert ldp.remote_bindings["2.2.2.2"]["10.0.0.0/24"] == 16000


def test_advertise_bindings_emits_current_local_mappings() -> None:
    ldp = LDPProcess(router_id="1.1.1.1")
    ldp.lib = {"10.0.0.0/24": 16, "10.1.0.0/24": 17}

    adverts = ldp.advertise_bindings()
    prefixes = {m.prefix for m in adverts}

    assert prefixes == {"10.0.0.0/24", "10.1.0.0/24"}


def test_build_lfib_returns_prefix_mapping() -> None:
    ldp = LDPProcess(router_id="1.1.1.1")
    ldp.lib = {"10.0.0.0/24": 16}
    ldp.remote_bindings = {"2.2.2.2": {"10.0.0.0/24": 16000}}

    lfib = ldp.build_lfib()
    assert lfib["10.0.0.0/24"][0] == 16000
