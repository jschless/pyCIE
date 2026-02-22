"""Protocol scaffolds used by labs."""

from .base import ProtocolBase
from .bfd import BFDProcess
from .bgp import BGPProcess
from .ldp import LDPProcess
from .ospf import OSPFProcess
from .stp import STPProcess
from .switching import LearningSwitch

__all__ = [
    "BFDProcess",
    "BGPProcess",
    "LDPProcess",
    "LearningSwitch",
    "OSPFProcess",
    "ProtocolBase",
    "STPProcess",
]
