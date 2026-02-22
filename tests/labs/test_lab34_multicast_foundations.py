"""Exercise tests for Lab 34 multicast foundations."""

from __future__ import annotations

import pytest

from pycie.protocols.multicast import MulticastProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab34]


def test_join_and_leave_update_group_membership() -> None:
    mcast = MulticastProcess()
    mcast.join_group("eth1", "239.1.1.1")
    mcast.join_group("eth2", "239.1.1.1")
    assert mcast.group_members["239.1.1.1"] == {"eth1", "eth2"}

    mcast.leave_group("eth1", "239.1.1.1")
    assert mcast.group_members["239.1.1.1"] == {"eth2"}


def test_leave_nonexistent_group_is_safe() -> None:
    mcast = MulticastProcess()
    mcast.leave_group("eth1", "239.255.0.1")
    assert mcast.group_members == {}


def test_rpf_uses_longest_prefix_match() -> None:
    mcast = MulticastProcess()
    mcast.install_rpf_route("10.0.0.0/8", "eth0")
    mcast.install_rpf_route("10.10.0.0/16", "eth1")

    assert mcast.expected_rpf_interface("10.10.1.1") == "eth1"
    assert mcast.expected_rpf_interface("10.200.1.1") == "eth0"


def test_rpf_check_failure_returns_no_egress() -> None:
    mcast = MulticastProcess()
    mcast.install_rpf_route("192.0.2.0/24", "eth0")
    mcast.join_group("eth2", "239.1.1.1")

    assert mcast.compute_egress_interfaces("192.0.2.55", "239.1.1.1", "eth3") == []


def test_compute_egress_excludes_ingress_and_is_sorted() -> None:
    mcast = MulticastProcess()
    mcast.install_rpf_route("198.51.100.0/24", "eth0")
    mcast.join_group("eth2", "239.1.1.1")
    mcast.join_group("eth1", "239.1.1.1")
    mcast.join_group("eth0", "239.1.1.1")

    egress = mcast.compute_egress_interfaces("198.51.100.2", "239.1.1.1", "eth0")
    assert egress == ["eth1", "eth2"]


def test_process_data_updates_sg_state() -> None:
    mcast = MulticastProcess()
    mcast.install_rpf_route("203.0.113.0/24", "eth0")
    mcast.join_group("eth1", "239.1.2.3")

    entry = mcast.process_data("203.0.113.2", "239.1.2.3", "eth0", now_ms=5)
    assert entry is not None
    assert entry.outgoing_ifs == ("eth1",)
    assert mcast.sg_state[("203.0.113.2", "239.1.2.3")].updated_at_ms == 5


def test_process_data_rejects_non_rpf_traffic() -> None:
    mcast = MulticastProcess()
    mcast.install_rpf_route("203.0.113.0/24", "eth0")
    mcast.join_group("eth1", "239.1.2.3")

    assert mcast.process_data("203.0.113.2", "239.1.2.3", "eth9", now_ms=5) is None


def test_process_data_tracks_empty_outgoing_state_when_no_members() -> None:
    mcast = MulticastProcess()
    mcast.install_rpf_route("203.0.113.0/24", "eth0")

    entry = mcast.process_data("203.0.113.2", "239.9.9.9", "eth0", now_ms=7)
    assert entry is not None
    assert entry.outgoing_ifs == ()
