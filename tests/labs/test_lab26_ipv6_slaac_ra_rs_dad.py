"""Exercise tests for Lab 26 IPv6 SLAAC RA/RS/DAD."""

from __future__ import annotations

import pytest

from pycie.protocols.ipv6_slaac import IPv6AddressState, IPv6SLAACProcess, RouterAdvertisement

pytestmark = [pytest.mark.exercise, pytest.mark.lab26]


def test_trigger_rs_and_emit_due_ra() -> None:
    proc = IPv6SLAACProcess()
    proc.configure_router("eth0", RouterAdvertisement(prefix="2001:db8:100::/64"))
    proc.trigger_rs("eth0", now_ms=100, response_delay_ms=20)

    assert proc.emit_due_ra(now_ms=119) == []
    emitted = proc.emit_due_ra(now_ms=120)
    assert len(emitted) == 1
    assert emitted[0][0] == "eth0"


def test_autoconfigure_from_ra_creates_tentative_address() -> None:
    proc = IPv6SLAACProcess()
    proc.configure_router("eth0", RouterAdvertisement(prefix="2001:db8:100::/64"))

    state = proc.autoconfigure_from_ra(if_name="eth0", host_mac="02:11:22:33:44:55", now_ms=1_000)
    assert state.state == IPv6AddressState.TENTATIVE
    assert state.address.startswith("2001:db8:100:")


def test_complete_dad_transitions_to_preferred() -> None:
    proc = IPv6SLAACProcess()
    proc.configure_router("eth0", RouterAdvertisement(prefix="2001:db8:100::/64"))
    tentative = proc.autoconfigure_from_ra(if_name="eth0", host_mac="02:11:22:33:44:55", now_ms=1_000)

    final = proc.complete_dad(tentative.address, conflict=False, now_ms=1_010)
    assert final.state == IPv6AddressState.PREFERRED


def test_complete_dad_conflict_marks_duplicate() -> None:
    proc = IPv6SLAACProcess()
    proc.configure_router("eth0", RouterAdvertisement(prefix="2001:db8:100::/64"))
    tentative = proc.autoconfigure_from_ra(if_name="eth0", host_mac="02:11:22:33:44:55", now_ms=1_000)

    final = proc.complete_dad(tentative.address, conflict=True, now_ms=1_010)
    assert final.state == IPv6AddressState.DUPLICATE
