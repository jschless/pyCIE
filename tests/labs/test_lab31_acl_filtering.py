"""Exercise tests for Lab 31 ACL filtering."""

from __future__ import annotations

import pytest

from pycie.protocols.acl import ACL, ACLAction, ACLPacket, ACLRule

pytestmark = [pytest.mark.exercise, pytest.mark.lab31]


def _pkt(**kwargs: object) -> ACLPacket:
    defaults = {
        "src_ip": "10.0.0.1",
        "dst_ip": "10.0.0.2",
        "protocol": "tcp",
        "src_port": 12345,
        "dst_port": 80,
    }
    defaults.update(kwargs)
    return ACLPacket(**defaults)


def test_implicit_deny_without_rules() -> None:
    acl = ACL()
    assert acl.evaluate(_pkt()) == ACLAction.DENY


def test_first_match_ordering_is_by_sequence() -> None:
    acl = ACL()
    acl.add_rule(ACLRule(seq=20, action=ACLAction.DENY, src_prefix="10.0.0.0/8"))
    acl.add_rule(ACLRule(seq=10, action=ACLAction.PERMIT, src_prefix="10.0.0.0/8"))

    assert acl.evaluate(_pkt(src_ip="10.5.5.5")) == ACLAction.PERMIT


def test_add_rule_replaces_existing_sequence() -> None:
    acl = ACL()
    acl.add_rule(ACLRule(seq=10, action=ACLAction.DENY, src_prefix="10.0.0.0/8"))
    acl.add_rule(ACLRule(seq=10, action=ACLAction.PERMIT, src_prefix="10.0.0.0/8"))

    assert len(acl.rules) == 1
    assert acl.evaluate(_pkt(src_ip="10.10.10.10")) == ACLAction.PERMIT


def test_protocol_specific_rule_and_ip_wildcard() -> None:
    acl = ACL()
    acl.add_rule(ACLRule(seq=10, action=ACLAction.PERMIT, protocol="icmp"))

    assert acl.evaluate(_pkt(protocol="icmp", src_port=None, dst_port=None)) == ACLAction.PERMIT
    assert acl.evaluate(_pkt(protocol="tcp")) == ACLAction.DENY


def test_src_and_dst_ports_must_match_when_configured() -> None:
    acl = ACL()
    acl.add_rule(ACLRule(seq=10, action=ACLAction.PERMIT, protocol="tcp", src_port=1024, dst_port=22))

    assert acl.evaluate(_pkt(src_port=1024, dst_port=22)) == ACLAction.PERMIT
    assert acl.evaluate(_pkt(src_port=1111, dst_port=22)) == ACLAction.DENY
    assert acl.evaluate(_pkt(src_port=1024, dst_port=80)) == ACLAction.DENY


def test_rule_removal_changes_decision() -> None:
    acl = ACL()
    acl.add_rule(ACLRule(seq=10, action=ACLAction.PERMIT, src_prefix="10.0.0.0/8"))
    assert acl.evaluate(_pkt(src_ip="10.1.1.1")) == ACLAction.PERMIT

    acl.remove_rule(10)
    assert acl.evaluate(_pkt(src_ip="10.1.1.1")) == ACLAction.DENY


def test_prefix_matching_for_source_and_destination() -> None:
    acl = ACL()
    acl.add_rule(
        ACLRule(
            seq=10,
            action=ACLAction.PERMIT,
            src_prefix="10.0.0.0/24",
            dst_prefix="192.0.2.0/24",
        )
    )

    assert acl.evaluate(_pkt(src_ip="10.0.0.44", dst_ip="192.0.2.99")) == ACLAction.PERMIT
    assert acl.evaluate(_pkt(src_ip="10.0.1.44", dst_ip="192.0.2.99")) == ACLAction.DENY


def test_ip_protocol_rule_matches_tcp_without_ports() -> None:
    acl = ACL()
    acl.add_rule(ACLRule(seq=10, action=ACLAction.PERMIT, protocol="ip", src_prefix="0.0.0.0/0"))

    assert acl.evaluate(_pkt(protocol="udp", src_port=123, dst_port=53)) == ACLAction.PERMIT
