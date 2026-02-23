"""Edge-case tests for Lab 27 QoS marking and queueing."""

from __future__ import annotations

import pytest

from pycie.protocols.qos_marking_queueing import QoSMarkingQueueingProcess, QoSPacket

pytestmark = [pytest.mark.exercise, pytest.mark.lab27]


def test_dequeue_returns_none_when_all_queues_are_empty() -> None:
    qos = QoSMarkingQueueingProcess()
    assert qos.dequeue() is None


def test_snapshot_depths_reports_all_known_queues() -> None:
    qos = QoSMarkingQueueingProcess()
    qos.enqueue(QoSPacket(packet_id="p1", dscp=46))
    qos.enqueue(QoSPacket(packet_id="p2", dscp=0))

    snapshot = qos.snapshot_depths()
    assert snapshot == {"priority": 1, "assured": 0, "best_effort": 1}


def test_best_effort_not_starved_under_weighted_round_robin() -> None:
    qos = QoSMarkingQueueingProcess()
    for i in range(8):
        qos.enqueue(QoSPacket(packet_id=f"hi{i}", dscp=46))
    qos.enqueue(QoSPacket(packet_id="be1", dscp=0))

    seen_ids: list[str] = []
    for _ in range(9):
        packet = qos.dequeue()
        if packet is not None:
            seen_ids.append(packet.packet_id)

    assert "be1" in seen_ids
