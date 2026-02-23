"""Lab 19: Simplified IKEv2 + Child SA lifecycle model."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from .base import ProtocolBase


class IKEv2Role(StrEnum):
    INITIATOR = "initiator"
    RESPONDER = "responder"


class IKEv2SAState(StrEnum):
    INIT = "init"
    IKE_ESTABLISHED = "ike_established"
    CHILD_ESTABLISHED = "child_established"
    DELETED = "deleted"


@dataclass(frozen=True)
class IKEv2Proposal:
    encryption: str
    integrity: str
    dh_group: str


@dataclass(frozen=True)
class ChildSelector:
    local_prefix: str
    remote_prefix: str
    protocol: str = "any"


@dataclass(frozen=True)
class ChildSA:
    child_sa_id: int
    selector: ChildSelector
    spi_in: int
    spi_out: int
    created_at_ms: int
    rekey_of: int | None = None
    active: bool = True


@dataclass
class IKEv2Session:
    peer_id: str
    role: "IKEv2Role | str"
    accepted_proposals: tuple[IKEv2Proposal, ...]
    local_id: str
    remote_id: str
    state: "IKEv2SAState | str" = IKEv2SAState.INIT
    chosen_proposal: IKEv2Proposal | None = None
    child_sas: dict[int, ChildSA] = field(default_factory=dict)
    next_child_sa_id: int = 1
    last_error: str | None = None

    def initiate(self, offered: IKEv2Proposal) -> bool:
        """Initiator selects one proposal and establishes IKE SA."""
        if self.state != IKEv2SAState.INIT:
            self.last_error = "session_not_initial"
            return False
        if offered not in self.accepted_proposals:
            self.last_error = "proposal_not_accepted"
            self.state = IKEv2SAState.DELETED
            return False
        self.chosen_proposal = offered
        self.state = IKEv2SAState.IKE_ESTABLISHED
        self.last_error = None
        return True

    def respond(self, offered: IKEv2Proposal) -> bool:
        """Responder validates proposal and transitions state."""
        return self.initiate(offered)

    def establish_child_sa(
        self,
        selector: ChildSelector,
        *,
        now_ms: int,
        spi_in: int,
        spi_out: int,
    ) -> ChildSA | None:
        """Create first child SA if selector is valid."""
        if self.state not in {IKEv2SAState.IKE_ESTABLISHED, IKEv2SAState.CHILD_ESTABLISHED}:
            self.last_error = "ike_sa_not_established"
            return None
        if not _selectors_compatible(selector):
            self.last_error = "selector_mismatch"
            return None
        child = ChildSA(
            child_sa_id=self.next_child_sa_id,
            selector=selector,
            spi_in=spi_in,
            spi_out=spi_out,
            created_at_ms=now_ms,
        )
        self.child_sas[child.child_sa_id] = child
        self.next_child_sa_id += 1
        self.state = IKEv2SAState.CHILD_ESTABLISHED
        self.last_error = None
        return child

    def rekey_child_sa(
        self,
        child_sa_id: int,
        *,
        now_ms: int,
        new_spi_in: int,
        new_spi_out: int,
        overlap_ms: int = 0,
    ) -> ChildSA | None:
        """Create replacement child SA, optionally overlapping old SA."""
        old = self.child_sas.get(child_sa_id)
        if old is None or not old.active:
            self.last_error = "child_sa_not_found"
            return None
        if self.state != IKEv2SAState.CHILD_ESTABLISHED:
            self.last_error = "child_sa_not_established"
            return None
        replacement = ChildSA(
            child_sa_id=self.next_child_sa_id,
            selector=old.selector,
            spi_in=new_spi_in,
            spi_out=new_spi_out,
            created_at_ms=now_ms,
            rekey_of=old.child_sa_id,
            active=True,
        )
        self.child_sas[replacement.child_sa_id] = replacement
        self.next_child_sa_id += 1
        if overlap_ms <= 0:
            self.child_sas[old.child_sa_id] = _inactive(old)
        self.last_error = None
        return replacement

    def age_rekey_overlap(self, *, now_ms: int, overlap_ms: int) -> None:
        """Deactivate old SAs once overlap window expires."""
        newest_by_parent: dict[int, ChildSA] = {}
        for child in self.child_sas.values():
            if child.rekey_of is None:
                continue
            existing = newest_by_parent.get(child.rekey_of)
            if existing is None or child.created_at_ms > existing.created_at_ms:
                newest_by_parent[child.rekey_of] = child

        for parent_id, newest in newest_by_parent.items():
            if now_ms - newest.created_at_ms >= overlap_ms:
                parent = self.child_sas.get(parent_id)
                if parent is not None and parent.active:
                    self.child_sas[parent_id] = _inactive(parent)

    def active_child_sas(self) -> list[ChildSA]:
        return sorted(
            (child for child in self.child_sas.values() if child.active),
            key=lambda child: child.child_sa_id,
        )

    def delete_session(self, *, reason: str) -> None:
        """Delete session and deactivate all child SAs."""
        for child_id, child in list(self.child_sas.items()):
            self.child_sas[child_id] = _inactive(child)
        self.state = IKEv2SAState.DELETED
        self.last_error = reason


@dataclass
class IKEv2Process(ProtocolBase):
    """Container process for lab-level session operations."""

    name: str = "ikev2_for_ipsec"
    sessions: dict[str, IKEv2Session] = field(default_factory=dict)

    def create_session(
        self,
        peer_id: str,
        *,
        role: "IKEv2Role | str",
        accepted_proposals: tuple[IKEv2Proposal, ...],
        local_id: str,
        remote_id: str,
    ) -> IKEv2Session:
        session = IKEv2Session(
            peer_id=peer_id,
            role=role,
            accepted_proposals=accepted_proposals,
            local_id=local_id,
            remote_id=remote_id,
        )
        self.sessions[peer_id] = session
        return session


def _selectors_compatible(selector: ChildSelector) -> bool:
    if selector.local_prefix == selector.remote_prefix:
        return False
    return "/" in selector.local_prefix and "/" in selector.remote_prefix


def _inactive(child: ChildSA) -> ChildSA:
    return ChildSA(
        child_sa_id=child.child_sa_id,
        selector=child.selector,
        spi_in=child.spi_in,
        spi_out=child.spi_out,
        created_at_ms=child.created_at_ms,
        rekey_of=child.rekey_of,
        active=False,
    )
