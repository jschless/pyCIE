"""Edge-case tests for Lab 31 ACL filtering."""

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


def test_port_rule_does_not_match_when_packet_ports_are_missing() -> None:
    acl = ACL()
    acl.add_rule(ACLRule(seq=10, action=ACLAction.PERMIT, protocol="tcp", src_port=12345, dst_port=80))

    assert acl.evaluate(_pkt(src_port=None, dst_port=80)) == ACLAction.DENY
    assert acl.evaluate(_pkt(src_port=12345, dst_port=None)) == ACLAction.DENY


def test_remove_missing_rule_is_noop() -> None:
    acl = ACL()
    acl.add_rule(ACLRule(seq=10, action=ACLAction.PERMIT, src_prefix="10.0.0.0/8"))
    acl.remove_rule(999)

    assert len(acl.rules) == 1
    assert acl.evaluate(_pkt(src_ip="10.20.30.40")) == ACLAction.PERMIT

