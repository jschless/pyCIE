"""Exercise tests for Lab 36 EVPN control plane."""

from __future__ import annotations

import pytest

from pycie.protocols.evpn import EVPNControlPlane, EVPNRoute, EVPNRouteType

pytestmark = [pytest.mark.exercise, pytest.mark.lab36]


def _rt2(vni: int, mac: str, nh: str, *, seq: int = 0, rt: str = "target:65000:5000", ip: str | None = None) -> EVPNRoute:
    return EVPNRoute(
        route_type=EVPNRouteType.RT2_MAC_IP,
        vni=vni,
        route_target=rt,
        next_hop=nh,
        mac=mac,
        ip=ip,
        sequence=seq,
        originator=nh,
    )


def _rt5(prefix: str, nh: str, *, rt: str = "target:65000:5000") -> EVPNRoute:
    return EVPNRoute(
        route_type=EVPNRouteType.RT5_IP_PREFIX,
        vni=5000,
        route_target=rt,
        next_hop=nh,
        prefix=prefix,
        originator=nh,
    )


def test_import_rejects_unmatched_route_target() -> None:
    cp = EVPNControlPlane(import_rts={"target:65000:5000"})
    route = _rt2(5000, "00:11:22:33:44:55", "192.0.2.10", rt="target:65000:9999")

    assert not cp.import_route("peer-a", route)
    assert cp.mac_rib == {}


def test_import_rt2_and_resolve_mac_next_hop() -> None:
    cp = EVPNControlPlane(import_rts={"target:65000:5000"})
    route = _rt2(5000, "00:11:22:33:44:55", "192.0.2.10")

    assert cp.import_route("peer-a", route)
    assert cp.resolve_mac(5000, "00:11:22:33:44:55") == "192.0.2.10"


def test_mac_mobility_prefers_higher_sequence() -> None:
    cp = EVPNControlPlane(import_rts={"target:65000:5000"})
    low = _rt2(5000, "00:11:22:33:44:55", "192.0.2.10", seq=10)
    high = _rt2(5000, "00:11:22:33:44:55", "192.0.2.20", seq=20)

    cp.import_route("peer-a", low)
    cp.import_route("peer-b", high)
    assert cp.resolve_mac(5000, "00:11:22:33:44:55") == "192.0.2.20"


def test_sequence_tie_prefers_lexicographically_lower_next_hop() -> None:
    cp = EVPNControlPlane(import_rts={"target:65000:5000"})
    a = _rt2(5000, "00:aa:bb:cc:dd:ee", "192.0.2.30", seq=100)
    b = _rt2(5000, "00:aa:bb:cc:dd:ee", "192.0.2.20", seq=100)

    cp.import_route("peer-a", a)
    cp.import_route("peer-b", b)
    assert cp.resolve_mac(5000, "00:aa:bb:cc:dd:ee") == "192.0.2.20"


def test_withdraw_route_falls_back_to_alternate_candidate() -> None:
    cp = EVPNControlPlane(import_rts={"target:65000:5000"})
    route_a = _rt2(5000, "00:11:22:33:44:55", "192.0.2.10", seq=10)
    route_b = _rt2(5000, "00:11:22:33:44:55", "192.0.2.20", seq=5)

    cp.import_route("peer-a", route_a)
    cp.import_route("peer-b", route_b)
    cp.withdraw_route("peer-a", route_a)

    assert cp.resolve_mac(5000, "00:11:22:33:44:55") == "192.0.2.20"


def test_import_rt5_and_resolve_prefix() -> None:
    cp = EVPNControlPlane(import_rts={"target:65000:5000"})
    route = _rt5("10.20.0.0/16", "192.0.2.99")

    cp.import_route("peer-a", route)
    assert cp.resolve_prefix("10.20.0.0/16") == "192.0.2.99"


def test_withdrawing_last_candidate_removes_mac_route() -> None:
    cp = EVPNControlPlane(import_rts={"target:65000:5000"})
    route = _rt2(5000, "00:11:22:33:44:55", "192.0.2.10")
    cp.import_route("peer-a", route)

    cp.withdraw_route("peer-a", route)
    assert cp.resolve_mac(5000, "00:11:22:33:44:55") is None


def test_same_mac_different_vni_kept_separate() -> None:
    cp = EVPNControlPlane(import_rts={"target:65000:5000"})
    cp.import_route("peer-a", _rt2(5000, "00:11:22:33:44:55", "192.0.2.10"))
    cp.import_route("peer-b", _rt2(6000, "00:11:22:33:44:55", "192.0.2.20"))

    assert cp.resolve_mac(5000, "00:11:22:33:44:55") == "192.0.2.10"
    assert cp.resolve_mac(6000, "00:11:22:33:44:55") == "192.0.2.20"
