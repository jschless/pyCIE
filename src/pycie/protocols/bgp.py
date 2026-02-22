"""Lab 04: simplified BGP protocol scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field

from pycie.core.todo import student_todo
from pycie.sim.network import Frame

from .base import ProtocolBase


@dataclass(frozen=True)
class BGPOpen:
    asn: int
    router_id: str
    hold_time_s: int


@dataclass(frozen=True)
class BGPUpdate:
    prefix: str
    next_hop: str
    as_path: tuple[int, ...]
    local_pref: int = 100
    med: int = 0
    origin: str = "IGP"


@dataclass
class BGPPeer:
    peer_id: str
    peer_as: int
    is_ibgp: bool
    state: str = "IDLE"
    hold_time_s: int = 90
    keepalive_s: int = 30


@dataclass
class BGPProcess(ProtocolBase):
    """Simplified BGP-4 process with deterministic best-path selection.

    Reading:
    - RFC 4271 sections 4-9
    - RFC 4456 route reflection basics
    """

    name: str = "bgp"
    local_as: int = 65000
    router_id: str = "0.0.0.0"
    peers: dict[str, BGPPeer] = field(default_factory=dict)
    adj_rib_in: dict[str, list[BGPUpdate]] = field(default_factory=dict)
    loc_rib: dict[str, BGPUpdate] = field(default_factory=dict)

    def on_start(self) -> None:
        """Attempt peer sessions and schedule keepalives."""
        student_todo("Start BGP sessions for configured peers")

    def on_frame(self, ingress_if: str, frame: Frame) -> None:
        """Dispatch OPEN/KEEPALIVE/UPDATE handling."""
        student_todo("Parse and process BGP message payloads")

    def establish_session(self, peer_id: str) -> None:
        """Drive peer FSM through OPEN/ESTABLISHED."""
        student_todo("Implement BGP peer finite state machine")

    def process_open(self, peer_id: str, open_msg: BGPOpen) -> None:
        """Validate and process OPEN from peer."""
        student_todo("Implement OPEN validation and peer negotiation")

    def process_update(self, peer_id: str, update: BGPUpdate) -> None:
        """Install update into Adj-RIB-In and trigger best-path."""
        student_todo("Implement Adj-RIB-In update handling")

    def best_path(self, prefix: str) -> BGPUpdate | None:
        """Return best path for prefix according to simplified tie-breakers."""
        student_todo("Implement deterministic BGP best-path algorithm")

    def recompute_loc_rib(self) -> None:
        """Rebuild Loc-RIB from Adj-RIB-In."""
        student_todo("Implement Loc-RIB recomputation")

    def export_updates_for_peer(self, peer_id: str) -> list[BGPUpdate]:
        """Return outbound updates after export policy."""
        student_todo("Implement export policy and outbound update build")
