#!/usr/bin/env python3
"""Generate a student scaffold by stripping marked solution blocks.

Usage:
    python tools/make_student_scaffold.py --input src/pycie --output dist/student/src/pycie

Any block between:
    # BEGIN_SOLUTION: short description
    ...
    # END_SOLUTION
is replaced with a `NotImplementedError` TODO.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil

BEGIN = "# BEGIN_SOLUTION"
END = "# END_SOLUTION"


def strip_solution_blocks(text: str) -> str:
    lines = text.splitlines(keepends=True)
    output: list[str] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        if BEGIN in line:
            indent = line.split("#", 1)[0]
            suffix = line.split(BEGIN, 1)[1].strip(" :\n")
            task = suffix if suffix else "implement this method"

            i += 1
            while i < len(lines) and END not in lines[i]:
                i += 1

            if i >= len(lines):
                raise ValueError("Unclosed solution block detected")

            output.append(
                f'{indent}raise NotImplementedError("TODO(student): {task}")\n'
            )
            i += 1
            continue

        output.append(line)
        i += 1

    return "".join(output)


def build_scaffold(input_dir: Path, output_dir: Path) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    shutil.copytree(input_dir, output_dir)

    for path in output_dir.rglob("*.py"):
        path.write_text(strip_solution_blocks(path.read_text()), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_scaffold(args.input, args.output)


if __name__ == "__main__":
    main()
