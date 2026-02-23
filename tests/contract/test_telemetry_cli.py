"""Contract tests for visualization CLI commands."""

from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from pycie.cli import main, run_pytest
from pycie.telemetry.events import EventType, Layer, SCHEMA_VERSION, TraceEvent
from pycie.telemetry.trace import write_trace_events


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
                    "        src_ip: 10.0.0.1",
                    "        dst_ip: 10.0.0.2",
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
            layer=Layer.SIM,
            event_type=EventType.FRAME_DELIVER,
            details={
                "src_node": "r1",
                "src_if": "eth0",
            },
        ),
        TraceEvent(
            schema_version=SCHEMA_VERSION,
            seq=4,
            ts_ms=1003,
            sim_time_ms=5,
            node="r2",
            ingress_if="eth1",
            packet_id="p1",
            layer=Layer.L2,
            event_type=EventType.FRAME_RX,
            details={
                "packet_summary": "EthernetII aa -> bb type=0x0800 | IPv4(10.0.0.1->10.0.0.2,ttl=64,proto=6)",
            },
        ),
        TraceEvent(
            schema_version=SCHEMA_VERSION,
            seq=5,
            ts_ms=1004,
            sim_time_ms=10,
            node="sw1",
            layer=Layer.STP,
            event_type=EventType.STP_ROOT_CHANGE,
            details={
                "old_root_id": "32768:00:00:00:00:00:0a",
                "new_root_id": "32768:00:00:00:00:00:01",
                "new_cost": 4,
                "root_port": "eth0",
            },
        ),
        TraceEvent(
            schema_version=SCHEMA_VERSION,
            seq=6,
            ts_ms=1005,
            sim_time_ms=11,
            node="sw1",
            layer=Layer.STP,
            event_type=EventType.STP_PORT_ROLE_CHANGE,
            details={
                "if_name": "eth1",
                "old_role": "DESIGNATED",
                "new_role": "ALTERNATE",
                "old_state": "FORWARDING",
                "new_state": "BLOCKING",
            },
        ),
    ]


def test_viz_replay_filters_by_event_node_packet_and_time(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trace = tmp_path / "trace.jsonl"
    write_trace_events(trace, _sample_trace_events())

    monkeypatch.chdir(repo_root)
    code = main(
        [
            "viz",
            "replay",
            "--trace",
            str(trace),
            "--event",
            "FRAME_TX",
            "--node",
            "r1",
            "--packet-id",
            "p1",
            "--from-ms",
            "0",
            "--to-ms",
            "0",
        ]
    )

    out = capsys.readouterr().out
    assert code == 0
    assert "FRAME_TX" in out
    assert "FRAME_RX" not in out


def test_viz_replay_full_detail_includes_packet_tree(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trace = tmp_path / "trace.jsonl"
    write_trace_events(trace, _sample_trace_events())

    monkeypatch.chdir(repo_root)
    code = main(["viz", "replay", "--trace", str(trace), "--event", "FRAME_TX", "--detail", "full"])

    out = capsys.readouterr().out
    assert code == 0
    assert "packet_tree:" in out
    assert "header[0]: IPv4" in out


def test_viz_packet_renders_life_of_packet(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trace = tmp_path / "trace.jsonl"
    write_trace_events(trace, _sample_trace_events())

    monkeypatch.chdir(repo_root)
    code = main(["viz", "packet", "--trace", str(trace), "--packet-id", "p1", "--detail", "packet"])

    out = capsys.readouterr().out
    assert code == 0
    assert "Packet p1" in out
    assert "r1" in out
    assert "r2" in out
    assert "packet:" in out


def test_viz_topology_shows_links_and_packet_location(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trace = tmp_path / "trace.jsonl"
    write_trace_events(trace, _sample_trace_events())

    monkeypatch.chdir(repo_root)
    code = main(["viz", "topology", "--trace", str(trace), "--packet-id", "p1"])

    out = capsys.readouterr().out
    assert code == 0
    assert "Topology snapshot" in out
    assert "r1:eth0 <-> r2:eth1" in out
    assert "Packet p1 location" in out


def test_viz_sequence_groups_output_by_time(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trace = tmp_path / "trace.jsonl"
    write_trace_events(trace, _sample_trace_events())

    monkeypatch.chdir(repo_root)
    code = main(["viz", "sequence", "--trace", str(trace), "--packet-id", "p1", "--detail", "packet"])

    out = capsys.readouterr().out
    assert code == 0
    assert "t=000000ms" in out
    assert "t=000005ms" in out
    assert "(+5ms)" in out


def test_viz_stp_reports_final_root_and_port_roles(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trace = tmp_path / "stp.jsonl"
    write_trace_events(trace, _sample_trace_events())

    monkeypatch.chdir(repo_root)
    code = main(["viz", "stp", "--trace", str(trace)])

    out = capsys.readouterr().out
    assert code == 0
    assert "Final root view" in out
    assert "sw1" in out
    assert "role=ALTERNATE" in out


def test_viz_replay_handles_no_matching_events(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trace = tmp_path / "trace.jsonl"
    write_trace_events(trace, _sample_trace_events())

    monkeypatch.chdir(repo_root)
    code = main(["viz", "replay", "--trace", str(trace), "--event", "FIB_DROP"])

    out = capsys.readouterr().out
    assert code == 0
    assert "No events matched" in out


def test_run_pytest_sets_trace_out_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, repo_root: Path) -> None:
    trace_path = tmp_path / "run_trace.jsonl"
    captured: dict[str, object] = {}

    def fake_run(cmd, cwd=None, env=None):
        captured["cmd"] = cmd
        captured["cwd"] = cwd
        captured["env"] = env
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    code = run_pytest(["-k", "nothing"], repo_root, trace_out=trace_path)

    assert code == 0
    assert captured["cwd"] == repo_root
    env = captured["env"]
    assert isinstance(env, dict)
    assert env["PYCIE_TRACE_OUT"] == str(trace_path.resolve())
