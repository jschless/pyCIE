"""Exercise tests for Lab 19 IKEv2 for IPsec."""

from __future__ import annotations

import pytest

from pycie.protocols.ikev2_for_ipsec import (
    ChildSelector,
    IKEv2Process,
    IKEv2Proposal,
    IKEv2SAState,
)

pytestmark = [pytest.mark.exercise, pytest.mark.lab19]


def _proposal() -> IKEv2Proposal:
    return IKEv2Proposal(encryption="aes256-gcm", integrity="sha256", dh_group="modp2048")


def _process_with_session():
    process = IKEv2Process()
    session = process.create_session(
        "peer1",
        role="initiator",
        accepted_proposals=(_proposal(),),
        local_id="local.example",
        remote_id="peer.example",
    )
    return process, session


def test_session_initiate_accepts_supported_proposal() -> None:
    _process, session = _process_with_session()
    assert session.initiate(_proposal())
    assert session.state == IKEv2SAState.IKE_ESTABLISHED


def test_establish_child_sa_after_ike_established() -> None:
    _process, session = _process_with_session()
    session.initiate(_proposal())

    child = session.establish_child_sa(
        ChildSelector(local_prefix="10.0.0.0/24", remote_prefix="10.1.0.0/24"),
        now_ms=1000,
        spi_in=5001,
        spi_out=9001,
    )
    assert child is not None
    assert session.state == IKEv2SAState.CHILD_ESTABLISHED
    assert child.child_sa_id == 1
    assert session.active_child_sas()[0].spi_out == 9001


def test_rekey_child_sa_with_overlap_keeps_old_and_new_active_until_aged() -> None:
    _process, session = _process_with_session()
    session.initiate(_proposal())
    session.establish_child_sa(
        ChildSelector(local_prefix="10.0.0.0/24", remote_prefix="10.1.0.0/24"),
        now_ms=1000,
        spi_in=5001,
        spi_out=9001,
    )

    replacement = session.rekey_child_sa(
        1,
        now_ms=2000,
        new_spi_in=5002,
        new_spi_out=9002,
        overlap_ms=5000,
    )
    assert replacement is not None
    active_ids = [child.child_sa_id for child in session.active_child_sas()]
    assert active_ids == [1, 2]

    session.age_rekey_overlap(now_ms=8000, overlap_ms=5000)
    active_ids = [child.child_sa_id for child in session.active_child_sas()]
    assert active_ids == [2]


def test_delete_session_deactivates_all_child_sas() -> None:
    _process, session = _process_with_session()
    session.initiate(_proposal())
    session.establish_child_sa(
        ChildSelector(local_prefix="10.0.0.0/24", remote_prefix="10.1.0.0/24"),
        now_ms=1000,
        spi_in=5001,
        spi_out=9001,
    )

    session.delete_session(reason="peer_delete")
    assert session.state == IKEv2SAState.DELETED
    assert session.active_child_sas() == []
