"""Command-line interface for pyCIE workflows."""

from __future__ import annotations

import argparse
import difflib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Sequence, TypeVar

from pycie.model.capabilities import CapabilityMatrix
from pycie.scenario import ScenarioRunner, load_scenario, render_scenario_report
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
from pycie.telemetry.webviz import write_web_visualization

EnumType = TypeVar("EnumType", Layer, EventType)

DEFAULT_SCAFFOLD_OUTPUT = Path("dist/student/src/pycie")
DEFAULT_REFERENCE_OUTPUT = Path("dist/reference/src/pycie")


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
    return sorted(raw.keys(), key=_lab_sort_key)


def _lab_sort_key(lab_id: str) -> tuple[int, str]:
    """Sort lab IDs like lab06, lab06a, lab06b, lab07 in deterministic order."""
    match = re.match(r"^lab(\d+)([a-z]*)$", lab_id)
    if match is None:
        return (10_000, lab_id)
    number = int(match.group(1))
    suffix = match.group(2)
    return (number, suffix)


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


def run_pytest(
    args: list[str],
    repo_root: Path,
    *,
    trace_out: Path | None = None,
    student_src: Path | None = None,
) -> int:
    """Run pytest with forwarded arguments."""
    cmd = [sys.executable, "-m", "pytest", *args]
    env = os.environ.copy()
    if trace_out is not None:
        trace_path = trace_out.expanduser().resolve()
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        env[TRACE_OUT_ENV] = str(trace_path)
        print(f"Trace output: {trace_path}")
    if student_src is not None:
        src_path = student_src.expanduser().resolve()
        env["PYCIE_SRC"] = str(src_path)
        print(f"Student source override: {src_path}")

    print("Running:", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=repo_root, env=env)
    return int(completed.returncode)


def is_likely_student_scaffold(src_root: Path) -> bool:
    """Return True when scaffold TODO markers are present across source files."""
    marker = "TODO(student):"
    marker_hits = 0
    for path in src_root.rglob("*.py"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        marker_hits += text.count(marker)
        if marker_hits >= 4:
            return True
    return False


def replace_tree(source: Path, destination: Path) -> None:
    """Replace destination directory with an exact copy of source."""
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)


def parse_lab_spec(spec: str, known_labs: set[str], *, option_name: str) -> set[str]:
    """Parse all/comma-separated lab selectors with validation."""
    normalized = spec.strip().lower()
    if normalized == "all":
        return set(known_labs)

    selected = {item.strip() for item in spec.split(",") if item.strip()}
    if not selected:
        raise ValueError(f"{option_name} cannot be empty; use 'all' or comma-separated lab ids")

    unknown = sorted(selected - known_labs)
    if unknown:
        raise ValueError(f"Unknown labs in {option_name}: {', '.join(unknown)}")
    return selected


def load_scaffold_target_files(repo_root: Path) -> dict[str, set[Path]]:
    """Load lab->file mappings from scaffold target configuration."""
    scaffold_script = (repo_root / "tools" / "make_student_scaffold.py").resolve()
    if not scaffold_script.exists():
        raise FileNotFoundError(f"Missing scaffold generator: {scaffold_script}")

    spec = importlib.util.spec_from_file_location("_pycie_scaffold_targets", scaffold_script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load scaffold generator: {scaffold_script}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    targets = getattr(module, "TARGETS", None)
    if targets is None:
        raise RuntimeError("Scaffold generator is missing TARGETS metadata")

    by_lab: dict[str, set[Path]] = {}
    for target in targets:
        lab = getattr(target, "lab", None)
        rel_path = getattr(target, "rel_path", None)
        if not isinstance(lab, str) or not isinstance(rel_path, str):
            continue
        by_lab.setdefault(lab, set()).add(Path(rel_path))
    return by_lab


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
    if namespace.student_src is None:
        default_src = (repo_root / "src" / "pycie").resolve()
        if not is_likely_student_scaffold(default_src):
            print(
                "Warning: running against solved reference source in src/pycie. "
                "Use `pycie scaffold --labs all` with `--student-src dist/student/src` "
                "or scaffold in place via `pycie scaffold --labs all --in-place`.",
                file=sys.stderr,
            )

    if namespace.target == "all":
        return run_pytest(
            ["-m", "exercise"],
            repo_root,
            trace_out=namespace.trace_out,
            student_src=namespace.student_src,
        )

    lab_ids = load_lab_ids(repo_root)
    lab_id = validate_lab_id(namespace.target, lab_ids)
    return run_pytest(
        ["-m", f"{lab_id} and exercise"],
        repo_root,
        trace_out=namespace.trace_out,
        student_src=namespace.student_src,
    )


def cmd_scaffold(namespace: argparse.Namespace, repo_root: Path) -> int:
    """Generate a student TODO scaffold from reference implementation."""
    input_src = (repo_root / "src" / "pycie").resolve()
    in_place = bool(namespace.in_place)
    if in_place:
        if namespace.output != DEFAULT_SCAFFOLD_OUTPUT:
            print("--output cannot be used with --in-place", file=sys.stderr)
            return 2
        output = input_src
    else:
        output = namespace.output.expanduser().resolve()
        if output == input_src:
            print("Refusing in-place scaffold without --in-place", file=sys.stderr)
            return 2

    if not in_place and namespace.no_reference_snapshot:
        print("--no-reference-snapshot is only valid with --in-place", file=sys.stderr)
        return 2
    if not in_place and namespace.reference_output != DEFAULT_REFERENCE_OUTPUT:
        print("--reference-output is only used with --in-place", file=sys.stderr)
        return 2

    reference_output = namespace.reference_output.expanduser().resolve()
    script = (repo_root / "tools" / "make_student_scaffold.py").resolve()
    scaffold_input = input_src
    reference_snapshotted = False
    temp_dir: tempfile.TemporaryDirectory[str] | None = None

    if in_place:
        if not namespace.no_reference_snapshot:
            if reference_output == output:
                print("--reference-output cannot match --output when scaffolding in place", file=sys.stderr)
                return 2
            replace_tree(input_src, reference_output)
            scaffold_input = reference_output
            reference_snapshotted = True
        else:
            temp_dir = tempfile.TemporaryDirectory(prefix="pycie-scaffold-")
            temp_input = Path(temp_dir.name) / "pycie"
            shutil.copytree(input_src, temp_input)
            scaffold_input = temp_input

    cmd = [
        sys.executable,
        str(script),
        "--input",
        str(scaffold_input),
        "--output",
        str(output),
        "--labs",
        namespace.labs,
    ]
    if namespace.strict:
        cmd.append("--strict")

    print("Running:", " ".join(cmd))
    try:
        completed = subprocess.run(cmd, cwd=repo_root)
        if completed.returncode != 0:
            return int(completed.returncode)
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()

    print(f"Scaffold generated: {output}")
    if in_place:
        if reference_snapshotted:
            print(f"Reference snapshot: {reference_output}")
            print("Restore solved source with: pycie restore")
        print("Use for lab runs: pycie run lab01")
    else:
        student_src = output.parent
        print(f"Use for lab runs: pycie run lab01 --student-src {student_src}")
    return 0


def cmd_restore(namespace: argparse.Namespace, repo_root: Path) -> int:
    """Restore in-place source tree from a saved reference snapshot."""
    reference = namespace.reference.expanduser().resolve()
    target = (repo_root / "src" / "pycie").resolve()

    if not reference.exists():
        print(f"Reference snapshot not found: {reference}", file=sys.stderr)
        return 1
    if reference == target:
        print("Reference snapshot path cannot equal src/pycie", file=sys.stderr)
        return 2

    if namespace.labs.strip().lower() == "all":
        replace_tree(reference, target)
        print(f"Restored source tree: {target}")
        return 0

    targets_by_lab = load_scaffold_target_files(repo_root)
    selected_labs = parse_lab_spec(namespace.labs, set(targets_by_lab.keys()), option_name="--labs")

    restored_files: set[Path] = set()
    for lab_id in sorted(selected_labs):
        for rel_path in sorted(targets_by_lab[lab_id], key=lambda item: item.as_posix()):
            source_path = reference / rel_path
            if not source_path.exists():
                print(f"Reference file missing for {lab_id}: {source_path}", file=sys.stderr)
                return 1
            destination_path = target / rel_path
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, destination_path)
            restored_files.add(rel_path)

    labs_display = ", ".join(sorted(selected_labs))
    print(f"Restored {len(restored_files)} file(s) for labs: {labs_display}")
    print(f"Reference snapshot: {reference}")
    print(f"Target source tree: {target}")
    print("Use this to run tests: pycie run lab01")
    return 0


def cmd_check(namespace: argparse.Namespace, repo_root: Path) -> int:
    """Run contract tests only (default pytest profile)."""
    del namespace
    return run_pytest([], repo_root)


def cmd_scenario_run(namespace: argparse.Namespace, repo_root: Path) -> int:
    """Run one scenario file and optionally write a report."""
    scenario_path = namespace.scenario_file.expanduser().resolve()
    scenario = load_scenario(scenario_path)
    matrix = CapabilityMatrix.from_json(repo_root / "labs" / "capabilities.json")
    runner = ScenarioRunner(capability_matrix=matrix)
    result = runner.run(scenario)

    status = "PASS" if result.passed else "FAIL"
    print(f"Scenario {scenario.name} ({scenario.lab_id}): {status}")
    print(
        f"Actions={len(scenario.actions)} Expectations={len(scenario.expectations)} "
        f"Failures={len(result.failures)}"
    )
    if result.failures:
        print("Failure details:")
        for failure in result.failures:
            print(f"  - {failure}")

    if namespace.report is not None:
        report_body = render_scenario_report(scenario, result, report_format=namespace.report)
        report_out = namespace.report_out
        if report_out is None:
            report_path = scenario_path.with_name(f"{scenario_path.stem}.report.{namespace.report}")
        else:
            report_path = report_out.expanduser().resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report_body, encoding="utf-8")
        print(f"Report written: {report_path}")

    return 0 if result.passed else 1


def cmd_guide(namespace: argparse.Namespace, repo_root: Path) -> int:
    """Print primary docs and recommended command entry points."""
    del namespace
    docs = [
        ("README", repo_root / "README.md"),
        ("Docs Home", repo_root / "docs" / "index.md"),
        ("Start Here", repo_root / "docs" / "getting_started.md"),
        ("Tutorial", repo_root / "docs" / "tutorial" / "index.md"),
        ("Docs Site", repo_root / "docs" / "docs_site.md"),
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
    print("  pycie scaffold --labs all")
    print("  pycie run lab01 --student-src dist/student/src")
    print("  pycie scaffold --labs all --in-place")
    print("  pycie run lab01")
    print("  pycie restore")
    print("  pycie scaffold --labs all --output dist/student/src/pycie")
    print("  pycie run lab01 --student-src dist/student/src")
    print("  pycie run lab01 --student-src dist/student/src --trace-out traces/lab01.jsonl")
    print("  pycie viz replay --trace traces/lab01.jsonl --detail packet")
    print("  pycie viz packet --trace traces/lab01.jsonl --packet-id p1")
    print("  pycie viz topology --trace traces/lab01.jsonl --packet-id p1")
    print("  pycie viz sequence --trace traces/lab01.jsonl --packet-id p1")
    print("  pycie viz stp --trace traces/lab02.jsonl")
    print("  pycie viz web --trace traces/lab01.jsonl --out dist/viz/lab01")
    print("  pycie scenario run labs/scenarios/lab16_dual_failure.json")
    print("  pip install -e '.[docs]'")
    print("  mkdocs serve")
    print("  mkdocs build --strict")
    print("  make bootstrap")
    print("  make run-foundations")
    print("  make docs-build")
    print("  pycie check")
    return 0


def cmd_quickstart(namespace: argparse.Namespace, repo_root: Path) -> int:
    """Print quickstart for first-time users."""
    del namespace
    print("pyCIE Quickstart")
    print("1) python -m venv .venv")
    print("2) source .venv/bin/activate")
    print("3) pip install -e '.[dev]'")
    print("4) pycie labs")
    print("5) pycie scaffold --labs all")
    print("6) pycie run lab01 --student-src dist/student/src")
    print("7) pycie run lab06a --student-src dist/student/src")
    print("8) pycie run lab06b --student-src dist/student/src")
    print("9) pycie run lab06c --student-src dist/student/src")
    print("10) pycie run lab01 --student-src dist/student/src --trace-out traces/lab01.jsonl")
    print("11) pycie viz replay --trace traces/lab01.jsonl --detail packet")
    print("12) pycie viz web --trace traces/lab01.jsonl --out dist/viz/lab01")
    print("13) pycie scenario run labs/scenarios/lab16_dual_failure.json")
    print()
    print("Start Here doc:", repo_root / "docs" / "getting_started.md")
    print("Tutorial map:", repo_root / "docs" / "tutorial" / "index.md")
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


def cmd_viz_web(namespace: argparse.Namespace, repo_root: Path) -> int:
    """Generate local static HTML viewer assets from trace JSONL."""
    del repo_root
    trace_path = namespace.trace.expanduser().resolve()
    output_dir = namespace.out.expanduser().resolve()
    events = load_trace_events(trace_path)
    artifacts = write_web_visualization(events, output_dir=output_dir, trace_path=trace_path)
    print(f"Web viewer generated: {artifacts['index']}")
    print(f"Open this file in a browser: {artifacts['index']}")
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
    p_run.add_argument(
        "--student-src",
        type=Path,
        help="Run tests against alternate src root (e.g. dist/student/src)",
    )
    p_run.set_defaults(func=cmd_run)

    p_scaffold = subparsers.add_parser("scaffold", help="Generate student TODO scaffold")
    p_scaffold.add_argument(
        "--labs",
        default="all",
        help="Comma-separated labs to strip (default: all)",
    )
    p_scaffold.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_SCAFFOLD_OUTPUT,
        help="Output scaffold package path (default: dist/student/src/pycie)",
    )
    p_scaffold.add_argument(
        "--in-place",
        action="store_true",
        help="Write scaffold into src/pycie (requires explicit opt-in)",
    )
    p_scaffold.add_argument(
        "--reference-output",
        type=Path,
        default=DEFAULT_REFERENCE_OUTPUT,
        help="Reference snapshot path used with --in-place (default: dist/reference/src/pycie)",
    )
    p_scaffold.add_argument(
        "--no-reference-snapshot",
        action="store_true",
        help="Do not save solved source snapshot when using --in-place",
    )
    p_scaffold.add_argument(
        "--strict",
        action="store_true",
        help="Fail if configured scaffold targets are missing",
    )
    p_scaffold.set_defaults(func=cmd_scaffold)

    p_restore = subparsers.add_parser("restore", help="Restore src/pycie from reference snapshot")
    p_restore.add_argument(
        "--reference",
        type=Path,
        default=DEFAULT_REFERENCE_OUTPUT,
        help="Reference snapshot path (default: dist/reference/src/pycie)",
    )
    p_restore.add_argument(
        "--labs",
        default="all",
        help="Comma-separated labs to restore (default: all)",
    )
    p_restore.set_defaults(func=cmd_restore)

    p_check = subparsers.add_parser("check", help="Run contract tests")
    p_check.set_defaults(func=cmd_check)

    p_guide = subparsers.add_parser("guide", help="Print important docs and commands")
    p_guide.set_defaults(func=cmd_guide)

    p_quickstart = subparsers.add_parser("quickstart", help="Print first-run setup steps")
    p_quickstart.set_defaults(func=cmd_quickstart)

    p_scenario = subparsers.add_parser("scenario", help="Run scenario fixtures and checks")
    scenario_subparsers = p_scenario.add_subparsers(dest="scenario_command", required=True)
    p_scenario_run = scenario_subparsers.add_parser("run", help="Run a scenario JSON file")
    p_scenario_run.add_argument("scenario_file", type=Path, help="Path to scenario JSON file")
    p_scenario_run.add_argument(
        "--report",
        choices=("json", "md"),
        help="Optional report format to export",
    )
    p_scenario_run.add_argument(
        "--report-out",
        type=Path,
        help="Optional report output path (default: alongside scenario file)",
    )
    p_scenario_run.set_defaults(func=cmd_scenario_run)

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

    p_web = viz_subparsers.add_parser("web", help="Generate static HTML trace viewer")
    p_web.add_argument("--trace", required=True, type=Path, help="Path to JSONL trace file")
    p_web.add_argument("--out", required=True, type=Path, help="Output directory for web assets")
    p_web.set_defaults(func=cmd_viz_web)

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
