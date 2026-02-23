"""Edge-case tests for Lab 34 multicast foundations."""

from __future__ import annotations

import pytest

from pycie.protocols.multicast import MulticastProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab34]


def test_expected_rpf_interface_tie_breaks_on_interface_name() -> None:
    mcast = MulticastProcess()
    mcast.install_rpf_route("10.0.0.0/8", "eth9")
    mcast.install_rpf_route("10.0.0.0/8", "eth1")

    assert mcast.expected_rpf_interface("10.1.1.1") == "eth1"


def test_process_data_refreshes_existing_sg_state() -> None:
    mcast = MulticastProcess()
    mcast.install_rpf_route("203.0.113.0/24", "eth0")
    mcast.join_group("eth1", "239.1.1.1")

    first = mcast.process_data("203.0.113.5", "239.1.1.1", "eth0", now_ms=10)
    assert first is not None

    mcast.join_group("eth2", "239.1.1.1")
    second = mcast.process_data("203.0.113.5", "239.1.1.1", "eth0", now_ms=20)
    assert second is not None
    assert second.updated_at_ms == 20
    assert second.outgoing_ifs == ("eth1", "eth2")

