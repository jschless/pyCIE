"""Edge-case tests for Lab 06 BFD."""

from __future__ import annotations

import pytest

from pycie.protocols.bfd import BFDControl, BFDProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab06]


def test_open_session_is_idempotent_for_same_peer() -> None:
    bfd = BFDProcess(discriminator_seed=100)
    first = bfd.open_session("2.2.2.2")
    second = bfd.open_session("2.2.2.2")

    assert first.local_discriminator == second.local_discriminator
    assert len(bfd.sessions) == 1


def test_receive_control_with_wrong_discriminator_is_ignored() -> None:
    bfd = BFDProcess(discriminator_seed=100)
    session = bfd.open_session("2.2.2.2")

    ctrl = BFDControl(
        your_discriminator=session.local_discriminator + 1,
        my_discriminator=777,
        state="UP",
        desired_min_tx_ms=300,
        required_min_rx_ms=300,
        detect_mult=3,
    )
    bfd.receive_control("2.2.2.2", ctrl)

    assert session.remote_discriminator == 0
    assert session.state == "DOWN"
