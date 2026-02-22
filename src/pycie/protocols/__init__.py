"""Protocol scaffolds used by labs."""

from .arp import ARPProcess
from .base import ProtocolBase
from .bfd import BFDProcess
from .bgp import BGPProcess
from .gre import GRETunnelProcess
from .ipsec import IPsecProcess
from .ldp import LDPProcess
from .mpls import MPLSProcess
from .ospf import OSPFProcess
from .policy import PolicyProcess
from .rstp import RSTPProcess
from .stp import STPProcess
from .switching import LearningSwitch
from .vrf import VRFProcess

__all__ = [
    "ARPProcess",
    "BFDProcess",
    "BGPProcess",
    "GRETunnelProcess",
    "IPsecProcess",
    "LDPProcess",
    "LearningSwitch",
    "MPLSProcess",
    "OSPFProcess",
    "PolicyProcess",
    "ProtocolBase",
    "RSTPProcess",
    "STPProcess",
    "VRFProcess",
]
