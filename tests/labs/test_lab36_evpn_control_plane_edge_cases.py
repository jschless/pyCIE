"""Edge-case tests for Lab 36 EVPN control plane."""

from __future__ import annotations

import pytest

from pycie.protocols.evpn import EVPNControlPlane, EVPNRoute, EVPNRouteType

pytestmark = [pytest.mark.exercise, pytest.mark.lab36]


def _rt2(vni: int, mac: str, nh: str, *, seq: int = 0, rt: str = "target:65000:5000") -> EVPNRoute:
    return EVPNRoute(
        route_type=EVPNRouteType.RT2_MAC_IP,
        vni=vni,
        route_target=rt,
        next_hop=nh,
        mac=mac,
        sequence=seq,
        originator=nh,
    )


def test_import_same_peer_same_route_key_replaces_previous_candidate() -> None:
    cp = EVPNControlPlane(import_rts={"target:65000:5000"})
    first = _rt2(5000, "00:11:22:33:44:55", "192.0.2.10", seq=1)
    second = _rt2(5000, "00:11:22:33:44:55", "192.0.2.20", seq=2)

    assert cp.import_route("peer-a", first)
    assert cp.import_route("peer-a", second)
    assert len(cp.adj_rib_in["peer-a"]) == 1
    assert cp.resolve_mac(5000, "00:11:22:33:44:55") == "192.0.2.20"


def test_withdraw_from_unknown_peer_is_noop() -> None:
    cp = EVPNControlPlane(import_rts={"target:65000:5000"})
    route = _rt2(5000, "00:11:22:33:44:55", "192.0.2.10")

    cp.withdraw_route("missing-peer", route)
    assert cp.mac_rib == {}
    assert cp.ip_rib == {}

