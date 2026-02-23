"""Edge-case tests for Lab 13 BGP policy."""

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


def test_no_matching_rule_defaults_to_deny() -> None:
    policy = RoutePolicy(
        name="IMPORT",
        rules=[
            RoutePolicyRule(
                sequence=10,
                matches=MatchConditions(prefix="192.0.2.0/24"),
                action=PolicyAction(permit=True),
            )
        ],
    )

    permitted, out = policy.evaluate(_route())
    assert not permitted
    assert out["prefix"] == "10.10.10.0/24"


def test_policy_chain_stops_on_deny() -> None:
    deny = RoutePolicy(
        name="DENY",
        rules=[RoutePolicyRule(sequence=5, matches=MatchConditions(community="65000:100"), action=PolicyAction(permit=False))],
    )
    mutate = RoutePolicy(
        name="MUTATE",
        rules=[RoutePolicyRule(sequence=10, matches=MatchConditions(prefix="10.10.10.0/24"), action=PolicyAction(permit=True, set_med=5))],
    )

    proc = PolicyProcess()
    proc.import_policies["192.0.2.2"] = [deny, mutate]

    permitted, out = proc.apply_import("192.0.2.2", _route())
    assert not permitted
    assert out["med"] == 50
