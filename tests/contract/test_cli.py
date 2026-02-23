"""Contract tests for the pyCIE CLI surface."""

from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from pycie.cli import build_parser, find_lab_readme, find_repo_root, load_lab_ids, main, validate_lab_id


@pytest.fixture()
def repo_root() -> Path:
    return find_repo_root(Path(__file__).resolve())


def test_load_lab_ids_includes_known_labs(repo_root: Path) -> None:
    lab_ids = load_lab_ids(repo_root)
    assert "lab01" in lab_ids
    assert "lab16" in lab_ids
    assert "lab39" in lab_ids


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
    assert namespace.output == Path("dist/student/src/pycie")
    assert namespace.strict is False


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
