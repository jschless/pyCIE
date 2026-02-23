"""Edge-case tests for Lab 14 VRF."""

from __future__ import annotations

import pytest

from pycie.protocols.vrf import VRF, VRFProcess, VRFRouteTarget

pytestmark = [pytest.mark.exercise, pytest.mark.lab14]


def test_bind_unknown_vrf_raises_key_error() -> None:
    proc = VRFProcess()

    with pytest.raises(KeyError):
        proc.bind_interface("MISSING", "eth0")


def test_rt_mismatch_prevents_route_leak() -> None:
    proc = VRFProcess()
    proc.create_vrf(VRF(name="A", rd="65000:1", rt=VRFRouteTarget("65000:100", "65000:100")))
    proc.create_vrf(VRF(name="B", rd="65000:2", rt=VRFRouteTarget("65000:200", "65000:200")))
    proc.install_route("A", "10.0.0.0/24", "192.0.2.1")

    proc.leak_route("A", "B", "10.0.0.0/24")
    assert "10.0.0.0/24" not in proc.vrfs["B"].routes
