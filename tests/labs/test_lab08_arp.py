"""Exercise tests for Lab 08 ARP."""

from __future__ import annotations

import pytest

from pycie.forwarding.arp import ARPTable
from pycie.model.packet import PacketStack
from pycie.protocols.arp import ARPMessage, ARPProcess

pytestmark = [pytest.mark.exercise, pytest.mark.lab08]


def test_arp_table_update_and_lookup() -> None:
    table = ARPTable()
    table.update("192.0.2.1", "aa:bb:cc:dd:ee:01", now_ms=100)

    assert table.lookup("192.0.2.1", now_ms=150) == "aa:bb:cc:dd:ee:01"


def test_arp_pending_queue_enqueue_and_drain() -> None:
    table = ARPTable()
    p1 = PacketStack(payload=b"a")
    p2 = PacketStack(payload=b"b")

    table.enqueue_pending("192.0.2.9", p1, now_ms=10)
    table.enqueue_pending("192.0.2.9", p2, now_ms=12)

    drained = table.drain_pending("192.0.2.9")
    assert [p.payload for p in drained] == [b"a", b"b"]


def test_needs_request_false_with_valid_entry() -> None:
    table = ARPTable()
    table.update("192.0.2.1", "aa:bb:cc:dd:ee:01", now_ms=100)

    assert not table.needs_request("192.0.2.1", now_ms=101)


def test_arp_message_builders() -> None:
    proc = ARPProcess()

    req = proc.build_request("192.0.2.10", "02:00:00:00:00:10", "192.0.2.11")
    rep = proc.build_reply(
        "192.0.2.11",
        "02:00:00:00:00:11",
        "192.0.2.10",
        "02:00:00:00:00:10",
    )

    assert isinstance(req, ARPMessage)
    assert req.opcode == "request"
    assert isinstance(rep, ARPMessage)
    assert rep.opcode == "reply"
