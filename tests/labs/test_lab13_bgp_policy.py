"""Exercise tests for Lab 13 policy processing."""

from __future__ import annotations

import pytest

from pycie.model.policy import MatchConditions, PolicyAction, RoutePolicy, RoutePolicyRule
from pycie.protocols.policy import PolicyProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab13]


def _route() -> dict[str, object]:
    return {
        "prefix": "10.10.10.0/24",
        "community": "65000:100",
        "neighbor": "192.0.2.2",
        "as_path": [65002, 64496],
        "local_pref": 100,
        "med": 50,
    }


def test_route_policy_permit_and_mutate() -> None:
    policy = RoutePolicy(
        name="IMPORT-INTERNET",
        rules=[
            RoutePolicyRule(
                sequence=10,
                matches=MatchConditions(prefix="10.10.10.0/24"),
                action=PolicyAction(permit=True, set_local_pref=250),
            )
        ],
    )

    permit, out = policy.evaluate(_route())
    assert permit
    assert out["local_pref"] == 250


def test_policy_process_chain_applies_in_order() -> None:
    policy = RoutePolicy(
        name="EXPORT",
        rules=[
            RoutePolicyRule(
                sequence=5,
                matches=MatchConditions(community="65000:100"),
                action=PolicyAction(permit=True, prepend_asn=65001, prepend_count=2),
            )
        ],
    )
    proc = PolicyProcess()
    proc.export_policies["192.0.2.2"] = [policy]

    permit, out = proc.apply_export("192.0.2.2", _route())
    assert permit
    assert len(out["as_path"]) == 4
