"""Command-line interface for pyCIE workflows."""

from __future__ import annotations

import argparse
import difflib
import json
from pathlib import Path
import subprocess
import sys
from typing import Sequence


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


def run_pytest(args: list[str], repo_root: Path) -> int:
    """Run pytest with forwarded arguments."""
    cmd = [sys.executable, "-m", "pytest", *args]
    print("Running:", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=repo_root)
    return int(completed.returncode)


def cmd_labs(namespace: argparse.Namespace, repo_root: Path) -> int:
    """List available labs with README path hints."""
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
        return run_pytest(["-m", "exercise"], repo_root)

    lab_ids = load_lab_ids(repo_root)
    lab_id = validate_lab_id(namespace.target, lab_ids)
    return run_pytest(["-m", f"{lab_id} and exercise"], repo_root)


def cmd_check(namespace: argparse.Namespace, repo_root: Path) -> int:
    """Run contract tests only (default pytest profile)."""
    return run_pytest([], repo_root)


def cmd_guide(namespace: argparse.Namespace, repo_root: Path) -> int:
    """Print primary docs and recommended command entry points."""
    docs = [
        ("README", repo_root / "README.md"),
        ("Usage Guide", repo_root / "docs" / "usage.md"),
        ("Lab Instructions", repo_root / "labs" / "INSTRUCTIONS.md"),
        ("Roadmap", repo_root / "docs" / "roadmap.md"),
        ("TODO", repo_root / "docs" / "TODO.md"),
    ]
    for label, path in docs:
        exists = "OK" if path.exists() else "MISSING"
        rel = path.relative_to(repo_root)
        print(f"{label:<16} {exists:<7} {rel}")

    print()
    print("Suggested commands:")
    print("  pycie labs")
    print("  pycie run lab01")
    print("  pycie run all")
    print("  pycie check")
    return 0


def cmd_quickstart(namespace: argparse.Namespace, repo_root: Path) -> int:
    """Print quickstart for first-time users."""
    print("pyCIE Quickstart")
    print("1) python -m venv .venv")
    print("2) source .venv/bin/activate")
    print("3) pip install -e .[dev]")
    print("4) pycie labs")
    print("5) pycie run lab01")
    print("6) pycie run all")
    print()
    print("If pycie command is unavailable, use: python -m pycie <subcommand>")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Create top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="pycie",
        description="CLI for pyCIE labs, tests, and docs.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_labs = subparsers.add_parser("labs", help="List labs available in this repo")
    p_labs.set_defaults(func=cmd_labs)

    p_show = subparsers.add_parser("show", help="Show README path for a lab")
    p_show.add_argument("lab_id", help="Lab id, e.g. lab01")
    p_show.set_defaults(func=cmd_show)

    p_run = subparsers.add_parser("run", help="Run exercise tests for a lab or all labs")
    p_run.add_argument("target", help="Lab id (e.g. lab07) or 'all'")
    p_run.set_defaults(func=cmd_run)

    p_check = subparsers.add_parser("check", help="Run contract tests")
    p_check.set_defaults(func=cmd_check)

    p_guide = subparsers.add_parser("guide", help="Print important docs and commands")
    p_guide.set_defaults(func=cmd_guide)

    p_quickstart = subparsers.add_parser("quickstart", help="Print first-run setup steps")
    p_quickstart.set_defaults(func=cmd_quickstart)

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
