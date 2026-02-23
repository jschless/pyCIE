"""Edge-case tests for Lab 04 BGP."""

from __future__ import annotations

import pytest

from pycie.protocols.bgp import BGPOpen, BGPPeer, BGPPeerState, BGPProcess, BGPUpdate

pytestmark = [pytest.mark.exercise, pytest.mark.lab04]


def test_process_open_with_wrong_as_resets_peer_to_idle() -> None:
    bgp = BGPProcess(local_as=65001, router_id="1.1.1.1")
    bgp.peers["2.2.2.2"] = BGPPeer("2.2.2.2", 65002, is_ibgp=False, state=BGPPeerState.ESTABLISHED)

    bgp.process_open("2.2.2.2", BGPOpen(asn=65099, router_id="2.2.2.2", hold_time_s=90))
    assert bgp.peers["2.2.2.2"].state == BGPPeerState.IDLE


def test_export_filters_paths_containing_peer_as() -> None:
    bgp = BGPProcess(local_as=65001, router_id="1.1.1.1")
    bgp.peers["2.2.2.2"] = BGPPeer("2.2.2.2", 65002, is_ibgp=False)
    bgp.loc_rib = {
        "10.0.0.0/24": BGPUpdate("10.0.0.0/24", "192.0.2.1", (65002, 65010), 100),
        "10.1.0.0/24": BGPUpdate("10.1.0.0/24", "192.0.2.2", (65010,), 100),
    }

    out = bgp.export_updates_for_peer("2.2.2.2")
    assert [u.prefix for u in out] == ["10.1.0.0/24"]
