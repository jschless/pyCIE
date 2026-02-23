"""Edge-case tests for Lab 19 IKEv2 for IPsec."""

from __future__ import annotations

import pytest

from pycie.protocols.ikev2_for_ipsec import (
    ChildSelector,
    IKEv2Proposal,
    IKEv2SAState,
    IKEv2Session,
)

pytestmark = [pytest.mark.exercise, pytest.mark.lab19]


def _proposal() -> IKEv2Proposal:
    return IKEv2Proposal(encryption="aes256-gcm", integrity="sha256", dh_group="modp2048")


def _session() -> IKEv2Session:
    return IKEv2Session(
        peer_id="peer1",
        role="initiator",
        accepted_proposals=(_proposal(),),
        local_id="local.example",
        remote_id="peer.example",
    )


def test_unsupported_proposal_fails_and_deletes_session() -> None:
    session = _session()
    bad = IKEv2Proposal(encryption="chacha20", integrity="sha512", dh_group="modp8192")

    assert not session.initiate(bad)
    assert session.state == IKEv2SAState.DELETED
    assert session.last_error == "proposal_not_accepted"


def test_child_sa_before_ike_established_fails() -> None:
    session = _session()

    child = session.establish_child_sa(
        ChildSelector(local_prefix="10.0.0.0/24", remote_prefix="10.1.0.0/24"),
        now_ms=1000,
        spi_in=5001,
        spi_out=9001,
    )
    assert child is None
    assert session.last_error == "ike_sa_not_established"


def test_selector_mismatch_rejected() -> None:
    session = _session()
    session.initiate(_proposal())

    child = session.establish_child_sa(
        ChildSelector(local_prefix="10.0.0.0/24", remote_prefix="10.0.0.0/24"),
        now_ms=1000,
        spi_in=5001,
        spi_out=9001,
    )
    assert child is None
    assert session.last_error == "selector_mismatch"


def test_rekey_missing_child_sa_fails() -> None:
    session = _session()
    session.initiate(_proposal())

    replacement = session.rekey_child_sa(
        99,
        now_ms=2000,
        new_spi_in=5002,
        new_spi_out=9002,
    )
    assert replacement is None
    assert session.last_error == "child_sa_not_found"
