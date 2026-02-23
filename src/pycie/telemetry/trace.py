"""Trace sinks, recorder, and JSONL helpers."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
import json
import os
from pathlib import Path
import time
from typing import Any, Iterable, Protocol, TextIO

from .events import EventType, Layer, SCHEMA_VERSION, TraceEvent

TRACE_OUT_ENV = "PYCIE_TRACE_OUT"


class TraceSink(Protocol):
    """Sink interface for trace storage."""

    def emit(self, event: TraceEvent) -> None:
        """Emit one telemetry event."""

    def close(self) -> None:
        """Release sink resources."""


class NoOpTraceSink:
    """Sink implementation that discards all events."""

    def emit(self, event: TraceEvent) -> None:
        del event

    def close(self) -> None:
        return


class MemoryTraceSink:
    """In-memory sink for unit tests."""

    def __init__(self) -> None:
        self.events: list[TraceEvent] = []

    def emit(self, event: TraceEvent) -> None:
        self.events.append(event)

    def close(self) -> None:
        return


class JsonlTraceSink:
    """JSONL sink where each line is one event object."""

    def __init__(self, path: str | Path, *, append: bool = False) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        self._handle: TextIO = self.path.open(mode, encoding="utf-8")

    def emit(self, event: TraceEvent) -> None:
        json.dump(event.to_dict(), self._handle, sort_keys=True)
        self._handle.write("\n")

    def close(self) -> None:
        self._handle.flush()
        self._handle.close()

    def __enter__(self) -> "JsonlTraceSink":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


class TraceRecorder:
    """Stateful event recorder that assigns sequence numbers."""

    def __init__(self, sink: TraceSink) -> None:
        self._sink = sink
        self._seq = 0

    def emit(
        self,
        *,
        sim_time_ms: float,
        node: str,
        layer: Layer | str,
        event_type: EventType | str,
        ingress_if: str | None = None,
        egress_if: str | None = None,
        packet_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> TraceEvent:
        """Create and emit one normalized event."""
        self._seq += 1
        event = TraceEvent(
            schema_version=SCHEMA_VERSION,
            seq=self._seq,
            ts_ms=int(time.time() * 1000),
            sim_time_ms=int(sim_time_ms),
            node=node,
            ingress_if=ingress_if,
            egress_if=egress_if,
            packet_id=packet_id,
            layer=Layer(layer),
            event_type=EventType(event_type),
            details={k: _normalize_detail(v) for k, v in (details or {}).items()},
        )
        self._sink.emit(event)
        return event

    def close(self) -> None:
        self._sink.close()


_ENV_RECORDERS: dict[Path, TraceRecorder] = {}


def recorder_from_env() -> TraceRecorder | None:
    """Return shared recorder configured via TRACE_OUT_ENV."""
    raw = os.environ.get(TRACE_OUT_ENV)
    if raw is None or not raw.strip():
        return None

    path = Path(raw).expanduser().resolve()
    recorder = _ENV_RECORDERS.get(path)
    if recorder is None:
        recorder = TraceRecorder(JsonlTraceSink(path))
        _ENV_RECORDERS[path] = recorder
    return recorder


def emit_from_env(
    *,
    sim_time_ms: float,
    node: str,
    layer: Layer | str,
    event_type: EventType | str,
    ingress_if: str | None = None,
    egress_if: str | None = None,
    packet_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> TraceEvent | None:
    """Emit one event to env-configured recorder when enabled."""
    recorder = recorder_from_env()
    if recorder is None:
        return None

    return recorder.emit(
        sim_time_ms=sim_time_ms,
        node=node,
        layer=layer,
        event_type=event_type,
        ingress_if=ingress_if,
        egress_if=egress_if,
        packet_id=packet_id,
        details=details,
    )


def close_env_recorders() -> None:
    """Close all environment-backed recorders (primarily for tests)."""
    for recorder in _ENV_RECORDERS.values():
        recorder.close()
    _ENV_RECORDERS.clear()


def load_trace_events(path: str | Path) -> list[TraceEvent]:
    """Load JSONL file into trace events."""
    events: list[TraceEvent] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            if not isinstance(raw, dict):
                raise ValueError("trace JSONL lines must decode to dictionaries")
            events.append(TraceEvent.from_dict(raw))
    return events


def write_trace_events(path: str | Path, events: Iterable[TraceEvent]) -> None:
    """Write events to JSONL path."""
    with JsonlTraceSink(path) as sink:
        for event in events:
            sink.emit(event)


def _normalize_detail(value: Any) -> Any:
    """Convert arbitrary Python values into JSON-friendly structures."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (list, tuple)):
        return [_normalize_detail(item) for item in value]
    if isinstance(value, set):
        return [_normalize_detail(item) for item in sorted(value, key=str)]
    if isinstance(value, dict):
        return {str(key): _normalize_detail(item) for key, item in value.items()}
    if is_dataclass(value):
        return {str(key): _normalize_detail(item) for key, item in asdict(value).items()}
    enum_value = getattr(value, "value", None)
    if isinstance(enum_value, (str, int, float, bool)):
        return enum_value
    return repr(value)
