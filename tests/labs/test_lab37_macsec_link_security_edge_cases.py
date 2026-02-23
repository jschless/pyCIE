"""Edge-case tests for Lab 37 MACsec link security."""

from __future__ import annotations

import pytest

from pycie.protocols.macsec import MACsecPayload, MACsecProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab37]


def test_validate_ingress_without_policy_fails() -> None:
    p = MACsecProcess()
    ok, reason = p.validate_ingress(
        "eth0",
        MACsecPayload(sak_id="sak1", packet_number=1, encrypted=True, payload=b"x"),
    )
    assert not ok
    assert reason == "no_policy"


def test_protect_egress_without_policy_fails() -> None:
    p = MACsecProcess()
    payload, reason = p.protect_egress("eth0", b"abc", packet_number=1)
    assert payload is None
    assert reason == "no_policy"

