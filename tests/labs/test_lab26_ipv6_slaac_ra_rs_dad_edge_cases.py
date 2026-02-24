"""Edge-case tests for Lab 26 IPv6 SLAAC RA/RS/DAD."""

from __future__ import annotations

import pytest

from pycie.protocols.ipv6_slaac import IPv6SLAACProcess, RouterAdvertisement, derive_eui64_interface_id

pytestmark = [pytest.mark.exercise, pytest.mark.lab26]


def test_autoconfigure_without_ra_raises() -> None:
    proc = IPv6SLAACProcess()
    with pytest.raises(ValueError, match="missing_router_advertisement"):
        proc.autoconfigure_from_ra(if_name="eth0", host_mac="02:11:22:33:44:55", now_ms=0)


def test_complete_dad_unknown_address_raises() -> None:
    proc = IPv6SLAACProcess()
    with pytest.raises(ValueError, match="unknown_slaac_address"):
        proc.complete_dad("2001:db8::1", conflict=False, now_ms=1)


def test_complete_dad_twice_raises() -> None:
    proc = IPv6SLAACProcess()
    proc.configure_router("eth0", RouterAdvertisement(prefix="2001:db8:100::/64"))
    tentative = proc.autoconfigure_from_ra(if_name="eth0", host_mac="02:11:22:33:44:55", now_ms=1_000)
    proc.complete_dad(tentative.address, conflict=False, now_ms=1_010)

    with pytest.raises(ValueError, match="dad_already_completed"):
        proc.complete_dad(tentative.address, conflict=False, now_ms=1_020)


def test_derive_eui64_interface_id_rejects_invalid_mac() -> None:
    with pytest.raises(ValueError, match="invalid_mac"):
        derive_eui64_interface_id("00:11:22")
