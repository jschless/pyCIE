"""Command-line interface for pyCIE workflows."""

from __future__ import annotations

import argparse
import difflib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Sequence, TypeVar

from pycie.telemetry.events import EventType, Layer
from pycie.telemetry.render import (
    DetailLevel,
    filter_events,
    render_packet_path,
    render_sequence,
    render_stp_summary,
    render_timeline,
    render_topology_snapshot,
)
from pycie.telemetry.trace import TRACE_OUT_ENV, load_trace_events

EnumType = TypeVar("EnumType", Layer, EventType)


def find_repo_root(start: Path | None = None) -> Path:
    """Find repository root by locating labs/capabilities.json."""
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "labs" / "capabilities.json").exists():
            return candidate
    raise FileNotFoundError("Could not locate repository root (missing labs/capabilities.json)")


def load_lab_ids(repo_root: Path) -> list[str]:
    """Return sorted lab IDs from capabilities file."""
    raw = json.loads((repo_root / "labs" / "capabilities.json").read_text(encoding="utf-8"))
    return sorted(raw.keys(), key=lambda lab_id: int(lab_id.removeprefix("lab")))


def find_lab_readme(repo_root: Path, lab_id: str) -> Path | None:
    """Find README path for a lab ID."""
    pattern = f"{lab_id}_*/README.md"
    matches = sorted((repo_root / "labs").glob(pattern))
    if matches:
        return matches[0]

    exact_dir = repo_root / "labs" / lab_id
    if (exact_dir / "README.md").exists():
        return exact_dir / "README.md"
    return None


def validate_lab_id(lab_id: str, valid_labs: Sequence[str]) -> str:
    """Validate lab id and provide actionable error on mismatch."""
    if lab_id in valid_labs:
        return lab_id

    suggestions = difflib.get_close_matches(lab_id, valid_labs, n=3)
    hint = ""
    if suggestions:
        hint = f" Did you mean: {', '.join(suggestions)}?"
    raise ValueError(f"Unknown lab id {lab_id!r}.{hint}")


def run_pytest(args: list[str], repo_root: Path, *, trace_out: Path | None = None) -> int:
    """Run pytest with forwarded arguments."""
    cmd = [sys.executable, "-m", "pytest", *args]
    env = os.environ.copy()
    if trace_out is not None:
        trace_path = trace_out.expanduser().resolve()
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        env[TRACE_OUT_ENV] = str(trace_path)
        print(f"Trace output: {trace_path}")

    print("Running:", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=repo_root, env=env)
    return int(completed.returncode)


def cmd_labs(namespace: argparse.Namespace, repo_root: Path) -> int:
    """List available labs with README path hints."""
    del namespace
    lab_ids = load_lab_ids(repo_root)
    for lab_id in lab_ids:
        readme = find_lab_readme(repo_root, lab_id)
        readme_display = str(readme.relative_to(repo_root)) if readme else "(README missing)"
        print(f"{lab_id:>5}  {readme_display}")
    return 0


def cmd_show(namespace: argparse.Namespace, repo_root: Path) -> int:
    """Show details for a single lab."""
    lab_ids = load_lab_ids(repo_root)
    lab_id = validate_lab_id(namespace.lab_id, lab_ids)
    readme = find_lab_readme(repo_root, lab_id)
    if readme is None:
        print(f"No README found for {lab_id}")
        return 1

    print(f"Lab: {lab_id}")
    print(f"README: {readme.relative_to(repo_root)}")
    print(f"Command: pycie run {lab_id}")
    return 0


def cmd_run(namespace: argparse.Namespace, repo_root: Path) -> int:
    """Run exercise tests for one lab or all labs."""
    if namespace.target == "all":
        return run_pytest(["-m", "exercise"], repo_root, trace_out=namespace.trace_out)

    lab_ids = load_lab_ids(repo_root)
    lab_id = validate_lab_id(namespace.target, lab_ids)
    return run_pytest(["-m", f"{lab_id} and exercise"], repo_root, trace_out=namespace.trace_out)


def cmd_check(namespace: argparse.Namespace, repo_root: Path) -> int:
    """Run contract tests only (default pytest profile)."""
    del namespace
    return run_pytest([], repo_root)


def cmd_guide(namespace: argparse.Namespace, repo_root: Path) -> int:
    """Print primary docs and recommended command entry points."""
    del namespace
    docs = [
        ("README", repo_root / "README.md"),
        ("Usage Guide", repo_root / "docs" / "usage.md"),
        ("Visualization Guide", repo_root / "docs" / "visualization.md"),
        ("Lab Instructions", repo_root / "labs" / "INSTRUCTIONS.md"),
        ("Roadmap", repo_root / "docs" / "roadmap.md"),
        ("TODO", repo_root / "docs" / "TODO.md"),
    ]
    for label, path in docs:
        exists = "OK" if path.exists() else "MISSING"
        rel = path.relative_to(repo_root)
        print(f"{label:<18} {exists:<7} {rel}")

    print()
    print("Suggested commands:")
    print("  pycie labs")
    print("  pycie run lab01")
    print("  pycie run lab01 --trace-out traces/lab01.jsonl")
    print("  pycie viz replay --trace traces/lab01.jsonl --detail packet")
    print("  pycie viz packet --trace traces/lab01.jsonl --packet-id p1")
    print("  pycie viz topology --trace traces/lab01.jsonl --packet-id p1")
    print("  pycie viz sequence --trace traces/lab01.jsonl --packet-id p1")
    print("  pycie viz stp --trace traces/lab02.jsonl")
    print("  pycie check")
    return 0


def cmd_quickstart(namespace: argparse.Namespace, repo_root: Path) -> int:
    """Print quickstart for first-time users."""
    del namespace, repo_root
    print("pyCIE Quickstart")
    print("1) python -m venv .venv")
    print("2) source .venv/bin/activate")
    print("3) pip install -e .[dev]")
    print("4) pycie labs")
    print("5) pycie run lab01")
    print("6) pycie run lab01 --trace-out traces/lab01.jsonl")
    print("7) pycie viz replay --trace traces/lab01.jsonl --detail packet")
    print("8) pycie viz topology --trace traces/lab01.jsonl --packet-id p1")
    print()
    print("If pycie command is unavailable, use: python -m pycie <subcommand>")
    return 0


def cmd_viz_replay(namespace: argparse.Namespace, repo_root: Path) -> int:
    """Replay trace in chronological event order."""
    del repo_root
    events = _load_filtered_events(namespace)
    lines = render_timeline(events, detail_level=_detail_level(namespace.detail))
    if not lines:
        print("No events matched the provided filters.")
        return 0
    print("\n".join(lines))
    return 0


def cmd_viz_packet(namespace: argparse.Namespace, repo_root: Path) -> int:
    """Render life-of-packet timeline for one packet id."""
    del repo_root
    events = load_trace_events(namespace.trace)
    lines = render_packet_path(events, namespace.packet_id, detail_level=_detail_level(namespace.detail))
    print("\n".join(lines))
    return 0


def cmd_viz_sequence(namespace: argparse.Namespace, repo_root: Path) -> int:
    """Render grouped time-sequence playback from trace."""
    del repo_root
    events = _load_filtered_events(namespace)
    lines = render_sequence(
        events,
        packet_id=namespace.packet_id,
        detail_level=_detail_level(namespace.detail),
    )
    print("\n".join(lines))
    return 0


def cmd_viz_topology(namespace: argparse.Namespace, repo_root: Path) -> int:
    """Render topology snapshot and packet location view."""
    del repo_root
    events = load_trace_events(namespace.trace)
    lines = render_topology_snapshot(
        events,
        at_seq=namespace.at_seq,
        packet_id=namespace.packet_id,
    )
    print("\n".join(lines))
    return 0


def cmd_viz_stp(namespace: argparse.Namespace, repo_root: Path) -> int:
    """Render STP election and role transition summary from trace."""
    del repo_root
    events = load_trace_events(namespace.trace)
    lines = render_stp_summary(events, bridge_id=namespace.bridge_id)
    print("\n".join(lines))
    return 0


def _load_filtered_events(namespace: argparse.Namespace) -> list:
    events = load_trace_events(namespace.trace)
    layers = _parse_enum_set(namespace.layers, Layer)
    event_types = _parse_enum_set(namespace.events, EventType)
    return filter_events(
        events,
        layers=layers,
        event_types=event_types,
        node=namespace.node,
        packet_id=namespace.packet_id,
        from_ms=namespace.from_ms,
        to_ms=namespace.to_ms,
    )


def _parse_enum_set(raw_values: Sequence[str] | None, enum_type: type[EnumType]) -> set[EnumType] | None:
    if not raw_values:
        return None

    parsed: set[EnumType] = set()
    valid = {value.value.lower(): value for value in enum_type}  # type: ignore[misc]
    for raw in raw_values:
        for token in raw.split(","):
            token = token.strip()
            if not token:
                continue
            normalized = token.lower()
            match = valid.get(normalized)
            if match is None:
                choices = ", ".join(sorted(valid.keys()))
                raise ValueError(f"Unknown {enum_type.__name__} value {token!r}. Choices: {choices}")
            parsed.add(match)
    return parsed


def _detail_level(value: str) -> DetailLevel:
    """Return validated render detail level from argparse value."""
    return value  # argparse `choices` guarantees this is a valid DetailLevel


def build_parser() -> argparse.ArgumentParser:
    """Create top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="pycie",
        description="CLI for pyCIE labs, tests, docs, and visualization.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_labs = subparsers.add_parser("labs", help="List labs available in this repo")
    p_labs.set_defaults(func=cmd_labs)

    p_show = subparsers.add_parser("show", help="Show README path for a lab")
    p_show.add_argument("lab_id", help="Lab id, e.g. lab01")
    p_show.set_defaults(func=cmd_show)

    p_run = subparsers.add_parser("run", help="Run exercise tests for a lab or all labs")
    p_run.add_argument("target", help="Lab id (e.g. lab07) or 'all'")
    p_run.add_argument(
        "--trace-out",
        type=Path,
        help="Write telemetry JSONL to this path while tests run",
    )
    p_run.set_defaults(func=cmd_run)

    p_check = subparsers.add_parser("check", help="Run contract tests")
    p_check.set_defaults(func=cmd_check)

    p_guide = subparsers.add_parser("guide", help="Print important docs and commands")
    p_guide.set_defaults(func=cmd_guide)

    p_quickstart = subparsers.add_parser("quickstart", help="Print first-run setup steps")
    p_quickstart.set_defaults(func=cmd_quickstart)

    p_viz = subparsers.add_parser("viz", help="Trace replay and packet-path visualization")
    viz_subparsers = p_viz.add_subparsers(dest="viz_command", required=True)

    p_replay = viz_subparsers.add_parser("replay", help="Replay trace events in time order")
    p_replay.add_argument("--trace", required=True, type=Path, help="Path to JSONL trace file")
    p_replay.add_argument("--node", help="Node filter")
    p_replay.add_argument(
        "--event",
        action="append",
        dest="events",
        help="EventType filter (repeatable or comma-separated)",
    )
    p_replay.add_argument(
        "--layer",
        action="append",
        dest="layers",
        help="Layer filter (repeatable or comma-separated)",
    )
    p_replay.add_argument("--packet-id", help="Packet correlation id filter")
    p_replay.add_argument("--from-ms", type=int, help="Start simulation time in ms")
    p_replay.add_argument("--to-ms", type=int, help="End simulation time in ms")
    p_replay.add_argument(
        "--detail",
        choices=("compact", "packet", "full"),
        default="compact",
        help="Render detail level for packet formatting",
    )
    p_replay.set_defaults(func=cmd_viz_replay)

    p_packet = viz_subparsers.add_parser("packet", help="Show life of one packet")
    p_packet.add_argument("--trace", required=True, type=Path, help="Path to JSONL trace file")
    p_packet.add_argument("--packet-id", required=True, help="Packet id to render")
    p_packet.add_argument(
        "--detail",
        choices=("compact", "packet", "full"),
        default="packet",
        help="Render detail level for packet formatting",
    )
    p_packet.set_defaults(func=cmd_viz_packet)

    p_sequence = viz_subparsers.add_parser("sequence", help="Show grouped event playback over time")
    p_sequence.add_argument("--trace", required=True, type=Path, help="Path to JSONL trace file")
    p_sequence.add_argument("--node", help="Node filter")
    p_sequence.add_argument(
        "--event",
        action="append",
        dest="events",
        help="EventType filter (repeatable or comma-separated)",
    )
    p_sequence.add_argument(
        "--layer",
        action="append",
        dest="layers",
        help="Layer filter (repeatable or comma-separated)",
    )
    p_sequence.add_argument("--packet-id", help="Packet correlation id filter")
    p_sequence.add_argument("--from-ms", type=int, help="Start simulation time in ms")
    p_sequence.add_argument("--to-ms", type=int, help="End simulation time in ms")
    p_sequence.add_argument(
        "--detail",
        choices=("compact", "packet", "full"),
        default="compact",
        help="Render detail level for packet formatting",
    )
    p_sequence.set_defaults(func=cmd_viz_sequence)

    p_topology = viz_subparsers.add_parser("topology", help="Show topology snapshot and packet position")
    p_topology.add_argument("--trace", required=True, type=Path, help="Path to JSONL trace file")
    p_topology.add_argument("--at-seq", type=int, help="Snapshot at or before this sequence number")
    p_topology.add_argument("--packet-id", help="Optional packet id to locate in snapshot")
    p_topology.set_defaults(func=cmd_viz_topology)

    p_stp = viz_subparsers.add_parser("stp", help="Show STP election and role transitions")
    p_stp.add_argument("--trace", required=True, type=Path, help="Path to JSONL trace file")
    p_stp.add_argument("--bridge-id", help="Optional bridge-id filter (priority:mac)")
    p_stp.set_defaults(func=cmd_viz_stp)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    namespace = parser.parse_args(argv)

    try:
        repo_root = find_repo_root()
        return int(namespace.func(namespace, repo_root))
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
