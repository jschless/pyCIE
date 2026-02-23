"""Exercise tests for Lab 27 QoS marking and queueing."""

from __future__ import annotations

import pytest

from pycie.protocols.qos_marking_queueing import QoSMarkingQueueingProcess, QoSPacket

pytestmark = [pytest.mark.exercise, pytest.mark.lab27]


def test_classify_dscp_maps_priority_assured_and_best_effort() -> None:
    qos = QoSMarkingQueueingProcess()

    assert qos.classify_dscp(46) == "priority"
    assert qos.classify_dscp(26) == "assured"
    assert qos.classify_dscp(0) == "best_effort"


def test_enqueue_and_dequeue_returns_packets_in_weighted_order() -> None:
    qos = QoSMarkingQueueingProcess()
    qos.enqueue(QoSPacket(packet_id="p1", dscp=46))
    qos.enqueue(QoSPacket(packet_id="p2", dscp=26))
    qos.enqueue(QoSPacket(packet_id="p3", dscp=0))

    out = [qos.dequeue(), qos.dequeue(), qos.dequeue()]
    ids = [packet.packet_id for packet in out if packet is not None]

    assert ids[0] == "p1"
    assert set(ids) == {"p1", "p2", "p3"}


def test_remark_updates_dscp_before_enqueue() -> None:
    qos = QoSMarkingQueueingProcess()
    packet = QoSPacket(packet_id="p1", dscp=0)

    remarked = qos.remark(packet, new_dscp=46)
    accepted, reason = qos.enqueue(remarked)

    assert accepted is True
    assert reason is None
    assert qos.queue_depth("priority") == 1


def test_queue_limit_enforced_with_drop_reason() -> None:
    qos = QoSMarkingQueueingProcess(queue_limits={"priority": 1, "assured": 64, "best_effort": 128})

    first = qos.enqueue(QoSPacket(packet_id="p1", dscp=46))
    second = qos.enqueue(QoSPacket(packet_id="p2", dscp=46))

    assert first == (True, None)
    assert second == (False, "queue_full")
