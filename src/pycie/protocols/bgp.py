"""Lab 04: simplified BGP protocol scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from pycie.sim.network import Frame
from pycie.telemetry.events import EventType, Layer

from .base import ProtocolBase


class BGPOrigin(StrEnum):
    IGP = "IGP"
    EGP = "EGP"
    INCOMPLETE = "INCOMPLETE"


class BGPPeerState(StrEnum):
    IDLE = "IDLE"
    ESTABLISHED = "ESTABLISHED"


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
    origin: "BGPOrigin | str" = BGPOrigin.IGP


@dataclass
class BGPPeer:
    peer_id: str
    peer_as: int
    is_ibgp: bool
    state: "BGPPeerState | str" = BGPPeerState.IDLE
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
        for peer_id in sorted(self.peers):
            self.establish_session(peer_id)

    def on_frame(self, ingress_if: str, frame: Frame) -> None:
        """Dispatch OPEN/KEEPALIVE/UPDATE handling."""
        payload = frame.payload
        if isinstance(payload, BGPOpen):
            self.process_open(ingress_if, payload)
        if isinstance(payload, BGPUpdate):
            self.process_update(ingress_if, payload)

    def establish_session(self, peer_id: str) -> None:
        """Drive peer FSM through OPEN/ESTABLISHED."""
        if peer_id not in self.peers:
            return
        peer = self.peers[peer_id]
        old_state = BGPPeerState(peer.state).value
        peer.state = BGPPeerState.ESTABLISHED
        self.emit_trace(
            layer=Layer.L3,
            event_type=EventType.BGP_SESSION_CHANGE,
            details={
                "peer_id": peer_id,
                "old_state": old_state,
                "new_state": BGPPeerState.ESTABLISHED.value,
                "reason": "start",
            },
        )

    def process_open(self, peer_id: str, open_msg: BGPOpen) -> None:
        """Validate and process OPEN from peer."""
        self.emit_trace(
            layer=Layer.L3,
            event_type=EventType.BGP_OPEN_RX,
            details={
                "peer_id": peer_id,
                "open_asn": open_msg.asn,
                "router_id": open_msg.router_id,
                "hold_time_s": open_msg.hold_time_s,
            },
        )
        peer = self.peers.get(peer_id)
        if peer is None:
            return
        old_state = BGPPeerState(peer.state).value
        if open_msg.asn != peer.peer_as:
            peer.state = BGPPeerState.IDLE
            self.emit_trace(
                layer=Layer.L3,
                event_type=EventType.BGP_SESSION_CHANGE,
                details={
                    "peer_id": peer_id,
                    "old_state": old_state,
                    "new_state": BGPPeerState.IDLE.value,
                    "reason": "asn_mismatch",
                    "expected_asn": peer.peer_as,
                    "received_asn": open_msg.asn,
                },
            )
            return
        peer.state = BGPPeerState.ESTABLISHED
        self.emit_trace(
            layer=Layer.L3,
            event_type=EventType.BGP_SESSION_CHANGE,
            details={
                "peer_id": peer_id,
                "old_state": old_state,
                "new_state": BGPPeerState.ESTABLISHED.value,
                "reason": "open_accepted",
            },
        )

    def process_update(self, peer_id: str, update: BGPUpdate) -> None:
        """Install update into Adj-RIB-In and trigger best-path."""
        self.emit_trace(
            layer=Layer.L3,
            event_type=EventType.BGP_UPDATE_RX,
            details={
                "peer_id": peer_id,
                "prefix": update.prefix,
                "next_hop": update.next_hop,
                "as_path": list(update.as_path),
                "local_pref": update.local_pref,
                "med": update.med,
                "origin": BGPOrigin(update.origin).value,
            },
        )
        bucket = self.adj_rib_in.setdefault(peer_id, [])
        bucket = [candidate for candidate in bucket if candidate.prefix != update.prefix]
        bucket.append(update)
        self.adj_rib_in[peer_id] = bucket
        self.recompute_loc_rib()

    def best_path(self, prefix: str) -> BGPUpdate | None:
        """Return best path for prefix according to simplified tie-breakers."""
        candidates: list[BGPUpdate] = []
        for updates in self.adj_rib_in.values():
            for update in updates:
                if update.prefix == prefix:
                    candidates.append(update)

        if not candidates:
            self.emit_trace(
                layer=Layer.L3,
                event_type=EventType.BGP_BEST_PATH,
                details={
                    "prefix": prefix,
                    "candidate_count": 0,
                    "selected_next_hop": None,
                    "reason": "no_candidates",
                },
            )
            return None

        ordered = sorted(
            candidates,
            key=lambda update: (
                -update.local_pref,
                len(update.as_path),
                update.med,
                update.next_hop,
                str(update.origin),
                update.as_path,
            ),
        )
        best = ordered[0]
        self.emit_trace(
            layer=Layer.L3,
            event_type=EventType.BGP_BEST_PATH,
            details={
                "prefix": prefix,
                "candidate_count": len(candidates),
                "selected_next_hop": best.next_hop,
                "selected_local_pref": best.local_pref,
                "selected_med": best.med,
                "selected_as_path_len": len(best.as_path),
                "reason": "local_pref_as_path_med_next_hop_origin",
            },
        )
        return best

    def recompute_loc_rib(self) -> None:
        """Rebuild Loc-RIB from Adj-RIB-In."""
        prefixes = {
            update.prefix
            for updates in self.adj_rib_in.values()
            for update in updates
        }

        self.loc_rib = {}
        for prefix in sorted(prefixes):
            best = self.best_path(prefix)
            if best is not None:
                self.loc_rib[prefix] = best

    def export_updates_for_peer(self, peer_id: str) -> list[BGPUpdate]:
        """Return outbound updates after export policy."""
        peer = self.peers.get(peer_id)
        if peer is None:
            return []

        out: list[BGPUpdate] = []
        for prefix in sorted(self.loc_rib):
            update = self.loc_rib[prefix]
            if peer.peer_as in update.as_path:
                continue
            out.append(update)
            self.emit_trace(
                layer=Layer.L3,
                event_type=EventType.BGP_UPDATE_EXPORT,
                details={
                    "peer_id": peer_id,
                    "prefix": update.prefix,
                    "next_hop": update.next_hop,
                    "as_path": list(update.as_path),
                },
            )
        return out
