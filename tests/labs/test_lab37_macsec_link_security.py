"""Exercise tests for Lab 37 MACsec link security."""

from __future__ import annotations

import pytest

from pycie.protocols.macsec import MACsecPayload, MACsecPolicy, MACsecProcess, SecureAssociation

pytestmark = [pytest.mark.exercise, pytest.mark.lab37]


def test_cleartext_rejected_when_encryption_required() -> None:
    p = MACsecProcess()
    p.configure_interface("eth0", MACsecPolicy(require_encryption=True))

    ok, reason = p.validate_ingress("eth0", MACsecPayload(sak_id="", packet_number=1, encrypted=False, payload=b"x"))
    assert not ok
    assert reason == "cleartext_not_allowed"


def test_cleartext_allowed_with_fallback() -> None:
    p = MACsecProcess()
    p.configure_interface("eth0", MACsecPolicy(require_encryption=True, allow_cleartext_fallback=True))

    ok, reason = p.validate_ingress("eth0", MACsecPayload(sak_id="", packet_number=1, encrypted=False, payload=b"x"))
    assert ok
    assert reason == "ok"


def test_encrypted_requires_active_secure_association() -> None:
    p = MACsecProcess()
    p.configure_interface("eth0", MACsecPolicy(require_encryption=True))

    ok, reason = p.validate_ingress("eth0", MACsecPayload(sak_id="sak1", packet_number=1, encrypted=True, payload=b"x"))
    assert not ok
    assert reason == "no_active_sa"


def test_sak_mismatch_is_rejected() -> None:
    p = MACsecProcess()
    p.configure_interface("eth0", MACsecPolicy(require_encryption=True))
    p.install_secure_association("eth0", SecureAssociation(peer_id="peer1", sak_id="sak-good"))

    ok, reason = p.validate_ingress("eth0", MACsecPayload(sak_id="sak-bad", packet_number=1, encrypted=True, payload=b"x"))
    assert not ok
    assert reason == "sak_mismatch"


def test_duplicate_packet_number_is_detected_as_replay() -> None:
    p = MACsecProcess()
    p.configure_interface("eth0", MACsecPolicy(require_encryption=True, replay_window=2))
    p.install_secure_association("eth0", SecureAssociation(peer_id="peer1", sak_id="sak1"))

    assert p.validate_ingress("eth0", MACsecPayload(sak_id="sak1", packet_number=10, encrypted=True, payload=b"x"))[0]
    ok, reason = p.validate_ingress("eth0", MACsecPayload(sak_id="sak1", packet_number=10, encrypted=True, payload=b"x"))
    assert not ok
    assert reason == "replay"


def test_out_of_order_within_replay_window_is_accepted() -> None:
    p = MACsecProcess()
    p.configure_interface("eth0", MACsecPolicy(require_encryption=True, replay_window=5))
    p.install_secure_association("eth0", SecureAssociation(peer_id="peer1", sak_id="sak1"))

    assert p.validate_ingress("eth0", MACsecPayload(sak_id="sak1", packet_number=10, encrypted=True, payload=b"x"))[0]
    ok, reason = p.validate_ingress("eth0", MACsecPayload(sak_id="sak1", packet_number=7, encrypted=True, payload=b"x"))
    assert ok
    assert reason == "ok"


def test_packet_too_old_outside_window_is_dropped() -> None:
    p = MACsecProcess()
    p.configure_interface("eth0", MACsecPolicy(require_encryption=True, replay_window=5))
    p.install_secure_association("eth0", SecureAssociation(peer_id="peer1", sak_id="sak1"))

    assert p.validate_ingress("eth0", MACsecPayload(sak_id="sak1", packet_number=20, encrypted=True, payload=b"x"))[0]
    ok, reason = p.validate_ingress("eth0", MACsecPayload(sak_id="sak1", packet_number=10, encrypted=True, payload=b"x"))
    assert not ok
    assert reason == "too_old"


def test_protect_egress_requires_sa_when_encryption_required() -> None:
    p = MACsecProcess()
    p.configure_interface("eth0", MACsecPolicy(require_encryption=True))

    packet, reason = p.protect_egress("eth0", b"abc", packet_number=1)
    assert packet is None
    assert reason == "no_active_sa"


def test_protect_egress_generates_cleartext_when_encryption_not_required() -> None:
    p = MACsecProcess()
    p.configure_interface("eth0", MACsecPolicy(require_encryption=False))

    packet, reason = p.protect_egress("eth0", b"abc", packet_number=1)
    assert packet is not None
    assert reason == "ok"
    assert not packet.encrypted
