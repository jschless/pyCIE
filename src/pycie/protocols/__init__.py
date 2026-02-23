"""Protocol scaffolds used by labs."""

from .aaa import AAAService
from .acl import ACL
from .arp import ARPProcess
from .base import ProtocolBase
from .bfd import BFDProcess
from .bgp_fsm_transport import BGPFSMState, BGPTransportProcess, BGPTransportSession
from .bgp import BGPProcess
from .control_plane_db import BGPDatabase, LDPDatabase, OSPFLSDB
from .dhcp import DHCPServer
from .evpn import EVPNControlPlane
from .gre import GRETunnelProcess
from .ipsec import IPsecProcess
from .isis import ISISProcess
from .ldp import LDPProcess
from .macsec import MACsecProcess
from .mpls import MPLSProcess
from .multicast import MulticastProcess
from .ospf import OSPFProcess
from .ospf_multi_area import OSPFMultiAreaProcess
from .policy import PolicyProcess
from .rib_fib_pipeline import RIBFIBPipeline
from .rstp import RSTPProcess
from .stp import STPProcess
from .switching import LearningSwitch
from .route_selection import RouteSelectionEngine
from .vrf import VRFProcess
from .vxlan import VXLANBridge

__all__ = [
    "AAAService",
    "ACL",
    "ARPProcess",
    "BGPDatabase",
    "BFDProcess",
    "BGPFSMState",
    "BGPProcess",
    "BGPTransportProcess",
    "BGPTransportSession",
    "DHCPServer",
    "EVPNControlPlane",
    "GRETunnelProcess",
    "IPsecProcess",
    "ISISProcess",
    "LDPDatabase",
    "LDPProcess",
    "LearningSwitch",
    "MACsecProcess",
    "MPLSProcess",
    "MulticastProcess",
    "OSPFProcess",
    "OSPFMultiAreaProcess",
    "OSPFLSDB",
    "PolicyProcess",
    "ProtocolBase",
    "RIBFIBPipeline",
    "RouteSelectionEngine",
    "RSTPProcess",
    "STPProcess",
    "VRFProcess",
    "VXLANBridge",
]
