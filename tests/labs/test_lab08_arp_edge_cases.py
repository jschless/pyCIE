"""Edge-case tests for Lab 08 ARP."""

from __future__ import annotations

import pytest

from pycie.forwarding.arp import ARPTable
from pycie.protocols.arp import ARPMessage, ARPProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab08]


def test_lookup_expires_entry_at_ttl_boundary() -> None:
    table = ARPTable()
    table.update("192.0.2.1", "aa:bb:cc:dd:ee:01", now_ms=10, ttl_ms=50)

    assert table.lookup("192.0.2.1", now_ms=60) is None
    assert "192.0.2.1" not in table.entries


def test_process_request_for_other_ip_learns_sender_without_reply() -> None:
    proc = ARPProcess()
    proc.local_ips["eth0"] = "192.0.2.10"
    proc.local_macs["eth0"] = "02:00:00:00:00:10"

    req = ARPMessage(
        opcode="request",
        sender_ip="192.0.2.20",
        sender_mac="02:00:00:00:00:20",
        target_ip="192.0.2.99",
    )
    proc.process_message("eth0", req)

    assert proc.ip_to_mac["192.0.2.20"] == "02:00:00:00:00:20"
    assert proc.outbound_messages == []
