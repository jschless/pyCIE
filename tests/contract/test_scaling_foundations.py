"""Contract checks for model/forwarding/scenario expansion."""

from __future__ import annotations

from pathlib import Path

from pycie.model.capabilities import CapabilityMatrix
from pycie.model.headers import IPv4Header
from pycie.model.packet import PacketStack
from pycie.protocols.arp import ARPProcess
from pycie.protocols.gre import GRETunnelProcess
from pycie.protocols.ipsec import IPsecProcess
from pycie.protocols.mpls import MPLSProcess
from pycie.protocols.policy import PolicyProcess
from pycie.protocols.rstp import RSTPProcess
from pycie.protocols.vrf import VRFProcess


def test_capability_matrix_file_loads() -> None:
    matrix = CapabilityMatrix.from_json(Path("labs/capabilities.json"))

    lab01 = matrix.for_lab("lab01")
    lab16 = matrix.for_lab("lab16")

    assert lab01.switching
    assert not lab01.gre
    assert lab16.gre
    assert lab16.ipsec
    assert lab16.mpls_forwarding


def test_packet_stack_push_pop_behavior() -> None:
    stack = PacketStack(payload=b"payload")
    stack.push_header(IPv4Header(src_ip="1.1.1.1", dst_ip="2.2.2.2", ttl=64, protocol=6))

    assert stack.peek_header() is not None
    popped = stack.pop_header()
    assert isinstance(popped, IPv4Header)
    assert stack.peek_header() is None


def test_new_protocol_classes_are_importable() -> None:
    assert ARPProcess().name == "arp"
    assert RSTPProcess().name == "rstp"
    assert GRETunnelProcess().name == "gre"
    assert IPsecProcess().name == "ipsec"
    assert PolicyProcess().name == "policy"
    assert VRFProcess().name == "vrf"
    assert MPLSProcess().name == "mpls"
