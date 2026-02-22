"""Lab 37: MACsec link-security model."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MACsecPolicy:
    require_encryption: bool = True
    replay_window: int = 0
    allow_cleartext_fallback: bool = False


@dataclass(frozen=True)
class SecureAssociation:
    peer_id: str
    sak_id: str
    active: bool = True


@dataclass(frozen=True)
class MACsecPayload:
    sak_id: str
    packet_number: int
    encrypted: bool
    payload: bytes


@dataclass
class MACsecProcess:
    """Per-interface MACsec policy and replay-protection checks."""

    policies: dict[str, MACsecPolicy] = field(default_factory=dict)
    secure_associations: dict[str, SecureAssociation] = field(default_factory=dict)
    highest_pn: dict[str, int] = field(default_factory=dict)
    seen_pn: dict[str, set[int]] = field(default_factory=dict)

    def configure_interface(self, if_name: str, policy: MACsecPolicy) -> None:
        self.policies[if_name] = policy

    def install_secure_association(self, if_name: str, association: SecureAssociation) -> None:
        self.secure_associations[if_name] = association

    def validate_ingress(self, if_name: str, packet: MACsecPayload) -> tuple[bool, str]:
        """Validate ingress packet against policy, SA, and replay rules."""
        policy = self.policies.get(if_name)
        if policy is None:
            return False, "no_policy"

        if not packet.encrypted:
            if policy.require_encryption and not policy.allow_cleartext_fallback:
                return False, "cleartext_not_allowed"
            return True, "ok"

        association = self.secure_associations.get(if_name)
        if association is None or not association.active:
            return False, "no_active_sa"
        if association.sak_id != packet.sak_id:
            return False, "sak_mismatch"

        highest = self.highest_pn.get(if_name, 0)
        seen = self.seen_pn.setdefault(if_name, set())
        if packet.packet_number in seen:
            return False, "replay"
        if highest and packet.packet_number + policy.replay_window < highest:
            return False, "too_old"

        seen.add(packet.packet_number)
        if packet.packet_number > highest:
            self.highest_pn[if_name] = packet.packet_number

        self._prune_replay_cache(if_name, policy)
        return True, "ok"

    def protect_egress(
        self,
        if_name: str,
        payload: bytes,
        *,
        packet_number: int,
    ) -> tuple[MACsecPayload | None, str]:
        """Build protected egress payload when policy allows transmission."""
        policy = self.policies.get(if_name)
        if policy is None:
            return None, "no_policy"

        association = self.secure_associations.get(if_name)
        if policy.require_encryption and (association is None or not association.active):
            return None, "no_active_sa"

        if not policy.require_encryption:
            return MACsecPayload(sak_id="", packet_number=packet_number, encrypted=False, payload=payload), "ok"

        assert association is not None
        return (
            MACsecPayload(
                sak_id=association.sak_id,
                packet_number=packet_number,
                encrypted=True,
                payload=payload,
            ),
            "ok",
        )

    def _prune_replay_cache(self, if_name: str, policy: MACsecPolicy) -> None:
        highest = self.highest_pn.get(if_name, 0)
        seen = self.seen_pn.get(if_name)
        if seen is None:
            return
        floor = max(0, highest - policy.replay_window - 1)
        self.seen_pn[if_name] = {pn for pn in seen if pn >= floor}
