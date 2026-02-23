"""Contract tests for static web visualization generation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pycie.cli import main
from pycie.telemetry.events import EventType, Layer, SCHEMA_VERSION, TraceEvent
from pycie.telemetry.trace import write_trace_events
from pycie.telemetry.webviz import normalize_trace_for_web


@pytest.fixture()
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _sample_trace_events() -> list[TraceEvent]:
    return [
        TraceEvent(
            schema_version=SCHEMA_VERSION,
            seq=1,
            ts_ms=1000,
            sim_time_ms=0,
            node="r1",
            egress_if="eth0",
            packet_id="p1",
            layer=Layer.L2,
            event_type=EventType.FRAME_TX,
            details={
                "packet_summary": "EthernetII aa -> bb type=0x0800 | IPv4(10.0.0.1->10.0.0.2,ttl=64,proto=6)",
                "packet_tree": [
                    "Ethernet II",
                    "  src_mac: aa",
                    "  dst_mac: bb",
                    "  payload:",
                    "    PacketStack",
                    "      header[0]: IPv4",
                ],
            },
        ),
        TraceEvent(
            schema_version=SCHEMA_VERSION,
            seq=2,
            ts_ms=1001,
            sim_time_ms=0,
            node="r1",
            egress_if="eth0",
            packet_id="p1",
            layer=Layer.SIM,
            event_type=EventType.FRAME_ENQUEUE,
            details={
                "src_node": "r1",
                "src_if": "eth0",
                "dst_node": "r2",
                "dst_if": "eth1",
                "latency_ms": 5,
            },
        ),
        TraceEvent(
            schema_version=SCHEMA_VERSION,
            seq=3,
            ts_ms=1002,
            sim_time_ms=5,
            node="r2",
            ingress_if="eth1",
            packet_id="p1",
            layer=Layer.L2,
            event_type=EventType.FRAME_RX,
            details={"packet_summary": "EthernetII aa -> bb type=0x0800"},
        ),
        TraceEvent(
            schema_version=SCHEMA_VERSION,
            seq=4,
            ts_ms=1003,
            sim_time_ms=6,
            node="r2",
            layer=Layer.L3,
            event_type=EventType.FIB_DROP,
            details={"drop_reason": "no_route"},
        ),
    ]


def test_normalize_trace_for_web_is_deterministic() -> None:
    events = _sample_trace_events()
    payload_a = normalize_trace_for_web(events, trace_path=Path("trace.jsonl"))
    payload_b = normalize_trace_for_web(list(reversed(events)), trace_path=Path("trace.jsonl"))

    assert payload_a == payload_b
    assert payload_a["topology"]["nodes"] == ["r1", "r2"]
    assert payload_a["packets"]["ids"] == ["p1"]
    assert payload_a["event_count"] == 4


def test_viz_web_generates_static_assets(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trace = tmp_path / "trace.jsonl"
    write_trace_events(trace, _sample_trace_events())
    out_dir = tmp_path / "viewer"

    monkeypatch.chdir(repo_root)
    code = main(["viz", "web", "--trace", str(trace), "--out", str(out_dir)])

    out = capsys.readouterr().out
    assert code == 0
    assert "Web viewer generated" in out

    index_path = out_dir / "index.html"
    styles_path = out_dir / "styles.css"
    viewer_path = out_dir / "viewer.js"
    data_json_path = out_dir / "data.json"
    data_js_path = out_dir / "data.js"

    assert index_path.exists()
    assert styles_path.exists()
    assert viewer_path.exists()
    assert data_json_path.exists()
    assert data_js_path.exists()

    index_html = index_path.read_text(encoding="utf-8")
    assert 'script src="data.js"' in index_html
    assert 'script src="viewer.js"' in index_html

    payload = json.loads(data_json_path.read_text(encoding="utf-8"))
    assert payload["event_count"] == 4
    assert payload["topology"]["nodes"] == ["r1", "r2"]
    assert payload["packets"]["ids"] == ["p1"]
    assert payload["events"][0]["seq"] == 1
