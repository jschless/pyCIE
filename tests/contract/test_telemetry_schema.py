"""Contract tests for telemetry schema and sinks."""

from __future__ import annotations

from pathlib import Path

import pytest

from pycie.telemetry.events import EventType, Layer, SCHEMA_VERSION, TraceEvent
from pycie.telemetry.trace import JsonlTraceSink, MemoryTraceSink, TraceRecorder, load_trace_events


def test_trace_event_round_trip_serialization() -> None:
    event = TraceEvent(
        schema_version=SCHEMA_VERSION,
        seq=7,
        ts_ms=12345,
        sim_time_ms=678,
        node="r1",
        ingress_if="eth0",
        egress_if="eth1",
        packet_id="p99",
        layer=Layer.L2,
        event_type=EventType.FRAME_TX,
        details={"dst_mac": "ff:ff:ff:ff:ff:ff", "egress_count": 2},
    )

    parsed = TraceEvent.from_dict(event.to_dict())
    assert parsed == event


def test_trace_event_rejects_unknown_layer_and_event_type() -> None:
    with pytest.raises(ValueError, match="unknown layer"):
        TraceEvent.from_dict(
            {
                "schema_version": 1,
                "seq": 1,
                "ts_ms": 1,
                "sim_time_ms": 1,
                "node": "r1",
                "layer": "invalid-layer",
                "event_type": EventType.FRAME_TX.value,
                "details": {},
            }
        )

    with pytest.raises(ValueError, match="unknown event_type"):
        TraceEvent.from_dict(
            {
                "schema_version": 1,
                "seq": 1,
                "ts_ms": 1,
                "sim_time_ms": 1,
                "node": "r1",
                "layer": Layer.L2.value,
                "event_type": "invalid-event",
                "details": {},
            }
        )


def test_trace_recorder_emits_monotonic_sequence_numbers() -> None:
    sink = MemoryTraceSink()
    recorder = TraceRecorder(sink)

    recorder.emit(sim_time_ms=10, node="r1", layer=Layer.SIM, event_type=EventType.FRAME_ENQUEUE)
    recorder.emit(sim_time_ms=12, node="r1", layer=Layer.SIM, event_type=EventType.FRAME_DELIVER)
    recorder.emit(sim_time_ms=15, node="r2", layer=Layer.L2, event_type=EventType.FRAME_RX)

    assert [event.seq for event in sink.events] == [1, 2, 3]


def test_jsonl_sink_close_flushes_to_disk(tmp_path: Path) -> None:
    path = tmp_path / "trace.jsonl"
    sink = JsonlTraceSink(path)
    recorder = TraceRecorder(sink)

    recorder.emit(sim_time_ms=1, node="r1", layer=Layer.L2, event_type=EventType.FRAME_TX)
    recorder.emit(sim_time_ms=2, node="r2", layer=Layer.L2, event_type=EventType.FRAME_RX)
    sink.close()

    loaded = load_trace_events(path)
    assert len(loaded) == 2
    assert loaded[0].event_type == EventType.FRAME_TX
    assert loaded[1].event_type == EventType.FRAME_RX


def test_trace_event_from_dict_handles_missing_optional_fields() -> None:
    parsed = TraceEvent.from_dict(
        {
            "schema_version": 1,
            "seq": 1,
            "ts_ms": 100,
            "sim_time_ms": 5,
            "node": "r1",
            "layer": Layer.SIM.value,
            "event_type": EventType.FRAME_DROP.value,
            "details": {"drop_reason": "no_link"},
        }
    )

    assert parsed.ingress_if is None
    assert parsed.egress_if is None
    assert parsed.packet_id is None
