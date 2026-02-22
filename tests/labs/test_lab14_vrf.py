"""Exercise tests for Lab 14 VRF."""

from __future__ import annotations

import pytest

from pycie.protocols.vrf import VRF, VRFProcess, VRFRouteTarget

pytestmark = [pytest.mark.exercise, pytest.mark.lab14]


def test_bind_interface_to_vrf() -> None:
    proc = VRFProcess()
    proc.create_vrf(VRF(name="CUST_A", rd="65000:1", rt=VRFRouteTarget("65000:100", "65000:100")))

    proc.bind_interface("CUST_A", "eth0")
    assert "eth0" in proc.vrfs["CUST_A"].interfaces


def test_route_leak_only_with_matching_targets() -> None:
    proc = VRFProcess()
    proc.create_vrf(VRF(name="A", rd="65000:1", rt=VRFRouteTarget("65000:100", "65000:100")))
    proc.create_vrf(VRF(name="B", rd="65000:2", rt=VRFRouteTarget("65000:100", "65000:200")))

    proc.install_route("A", "10.0.0.0/24", "192.0.2.1")
    proc.leak_route("A", "B", "10.0.0.0/24")

    assert proc.vrfs["B"].routes["10.0.0.0/24"] == "192.0.2.1"
