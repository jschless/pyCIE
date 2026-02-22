"""Contract tests for the pyCIE CLI surface."""

from __future__ import annotations

from pathlib import Path

import pytest

from pycie.cli import find_lab_readme, find_repo_root, load_lab_ids, main, validate_lab_id


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
