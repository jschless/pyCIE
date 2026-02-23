"""Contract tests for the pyCIE CLI surface."""

from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from pycie.cli import _lab_sort_key, build_parser, find_lab_readme, find_repo_root, load_lab_ids, main, validate_lab_id


@pytest.fixture()
def repo_root() -> Path:
    return find_repo_root(Path(__file__).resolve())


def test_load_lab_ids_includes_known_labs(repo_root: Path) -> None:
    lab_ids = load_lab_ids(repo_root)
    assert "lab01" in lab_ids
    assert "lab16" in lab_ids
    assert "lab39" in lab_ids
    assert "lab06a" in lab_ids
    assert "lab06b" in lab_ids
    assert "lab06c" in lab_ids


def test_lab_sort_key_orders_suffix_labs_after_numeric_base() -> None:
    ordered = sorted(["lab07", "lab06c", "lab06", "lab06b", "lab06a"], key=_lab_sort_key)
    assert ordered == ["lab06", "lab06a", "lab06b", "lab06c", "lab07"]


def test_find_lab_readme_returns_expected_path(repo_root: Path) -> None:
    readme = find_lab_readme(repo_root, "lab01")
    assert readme is not None
    assert readme.name == "README.md"
    assert "lab01_" in readme.parent.name


def test_validate_lab_id_suggests_close_matches() -> None:
    with pytest.raises(ValueError) as exc:
        validate_lab_id("lab1", ["lab01", "lab02", "lab10"])

    message = str(exc.value)
    assert "Unknown lab id" in message
    assert "Did you mean" in message


def test_cli_main_labs_lists_and_returns_success(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], repo_root: Path) -> None:
    monkeypatch.chdir(repo_root)

    exit_code = main(["labs"])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "lab01" in out


def test_cli_main_rejects_unknown_lab(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], repo_root: Path) -> None:
    monkeypatch.chdir(repo_root)

    exit_code = main(["run", "lab999"])
    err = capsys.readouterr().err

    assert exit_code == 2
    assert "Unknown lab id" in err


def test_build_parser_accepts_student_src_on_run() -> None:
    parser = build_parser()
    namespace = parser.parse_args(["run", "lab01", "--student-src", "dist/student/src"])

    assert namespace.target == "lab01"
    assert namespace.student_src == Path("dist/student/src")


def test_build_parser_accepts_scaffold_defaults() -> None:
    parser = build_parser()
    namespace = parser.parse_args(["scaffold"])

    assert namespace.labs == "all"
    assert namespace.output == Path("src/pycie")
    assert namespace.reference_output == Path("dist/reference/src/pycie")
    assert namespace.no_reference_snapshot is False
    assert namespace.strict is False


def test_build_parser_accepts_restore_defaults() -> None:
    parser = build_parser()
    namespace = parser.parse_args(["restore"])

    assert namespace.reference == Path("dist/reference/src/pycie")
    assert namespace.labs == "all"


def test_build_parser_accepts_restore_labs_selector() -> None:
    parser = build_parser()
    namespace = parser.parse_args(["restore", "--labs", "lab01,lab07"])

    assert namespace.labs == "lab01,lab07"


def test_build_parser_accepts_viz_web_arguments() -> None:
    parser = build_parser()
    namespace = parser.parse_args(["viz", "web", "--trace", "trace.jsonl", "--out", "dist/viz/lab01"])

    assert namespace.trace == Path("trace.jsonl")
    assert namespace.out == Path("dist/viz/lab01")


def test_build_parser_accepts_scenario_run_arguments() -> None:
    parser = build_parser()
    namespace = parser.parse_args(
        [
            "scenario",
            "run",
            "labs/scenarios/lab16_dual_failure.json",
            "--report",
            "json",
            "--report-out",
            "dist/reports/lab16.json",
        ]
    )

    assert namespace.scenario_file == Path("labs/scenarios/lab16_dual_failure.json")
    assert namespace.report == "json"
    assert namespace.report_out == Path("dist/reports/lab16.json")


def test_cli_main_scaffold_invokes_generator(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
    tmp_path: Path,
) -> None:
    captured: dict[str, object] = {}

    def fake_run(cmd, cwd=None):
        captured["cmd"] = cmd
        captured["cwd"] = cwd
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.chdir(repo_root)
    output = tmp_path / "student" / "src" / "pycie"

    exit_code = main(["scaffold", "--labs", "lab01", "--output", str(output)])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert captured["cwd"] == repo_root
    cmd = captured["cmd"]
    assert isinstance(cmd, list)
    assert "--labs" in cmd
    assert "lab01" in cmd
    assert "--output" in cmd
    assert str(output.resolve()) in cmd
    assert "Use for lab runs: pycie run lab01 --student-src" in out


def test_cli_main_scaffold_in_place_snapshots_reference(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
) -> None:
    captured: dict[str, object] = {}

    def fake_replace_tree(source: Path, destination: Path) -> None:
        captured["source"] = source
        captured["destination"] = destination

    def fake_run(cmd, cwd=None):
        captured["cmd"] = cmd
        captured["cwd"] = cwd
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr("pycie.cli.replace_tree", fake_replace_tree)
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.chdir(repo_root)

    exit_code = main(["scaffold"])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert captured["cwd"] == repo_root
    assert captured["source"] == (repo_root / "src" / "pycie").resolve()
    assert captured["destination"] == (repo_root / "dist" / "reference" / "src" / "pycie").resolve()
    cmd = captured["cmd"]
    assert isinstance(cmd, list)
    assert "--input" in cmd
    assert str((repo_root / "dist" / "reference" / "src" / "pycie").resolve()) in cmd
    assert "--output" in cmd
    assert str((repo_root / "src" / "pycie").resolve()) in cmd
    assert "Restore solved source with: pycie restore" in out
    assert "Use for lab runs: pycie run lab01" in out


def test_cli_main_restore_labs_restores_selected_files(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
    tmp_path: Path,
) -> None:
    reference = tmp_path / "reference" / "src" / "pycie"
    source_file = reference / "forwarding" / "l3.py"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text("# solved", encoding="utf-8")

    copied: list[tuple[Path, Path]] = []

    def fake_copy2(source: Path, destination: Path) -> None:
        copied.append((Path(source), Path(destination)))

    monkeypatch.setattr("pycie.cli.load_scaffold_target_files", lambda _: {"lab07": {Path("forwarding/l3.py")}})
    monkeypatch.setattr("pycie.cli.shutil.copy2", fake_copy2)
    monkeypatch.chdir(repo_root)

    exit_code = main(["restore", "--reference", str(reference), "--labs", "lab07"])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert len(copied) == 1
    assert copied[0][0] == source_file.resolve()
    assert copied[0][1] == (repo_root / "src" / "pycie" / "forwarding" / "l3.py").resolve()
    assert "Restored 1 file(s) for labs: lab07" in out


def test_cli_main_restore_labs_rejects_unknown_lab(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
    tmp_path: Path,
) -> None:
    reference = tmp_path / "reference" / "src" / "pycie"
    reference.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("pycie.cli.load_scaffold_target_files", lambda _: {"lab07": {Path("forwarding/l3.py")}})
    monkeypatch.chdir(repo_root)

    exit_code = main(["restore", "--reference", str(reference), "--labs", "lab99"])
    err = capsys.readouterr().err

    assert exit_code == 2
    assert "Unknown labs in --labs" in err
