"""Exercise tests for Lab 06 BFD."""

from __future__ import annotations

import pytest

from pycie.protocols.bfd import BFDControl, BFDProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab06]


def test_open_session_assigns_unique_discriminator() -> None:
    bfd = BFDProcess(discriminator_seed=100)

    a = bfd.open_session("2.2.2.2")
    b = bfd.open_session("3.3.3.3")

    assert a.local_discriminator != b.local_discriminator


def test_detect_time_ms_uses_multiplier_and_rx_interval() -> None:
    bfd = BFDProcess(discriminator_seed=100)
    session = bfd.open_session("2.2.2.2")
    session.required_min_rx_ms = 250
    session.detect_mult = 4

    assert bfd.detect_time_ms("2.2.2.2") == 1000


def test_receive_control_updates_remote_discriminator_and_state() -> None:
    bfd = BFDProcess(discriminator_seed=100)
    session = bfd.open_session("2.2.2.2")

    ctrl = BFDControl(
        your_discriminator=session.local_discriminator,
        my_discriminator=777,
        state="UP",
        desired_min_tx_ms=300,
        required_min_rx_ms=300,
        detect_mult=3,
    )

    bfd.receive_control("2.2.2.2", ctrl)
    assert session.remote_discriminator == 777
    assert session.state in {"INIT", "UP"}


def test_check_timeouts_reports_expired_sessions() -> None:
    bfd = BFDProcess(discriminator_seed=100)
    session = bfd.open_session("2.2.2.2")
    session.required_min_rx_ms = 100
    session.detect_mult = 3
    session.last_rx_ms = 0

    # simulate passage of time
    bfd.device = type("FakeDevice", (), {"simulator": type("FakeSim", (), {"clock": type("FakeClock", (), {"now_ms": 350})()})()})()

    expired = bfd.check_timeouts()
    assert expired == ["2.2.2.2"]
