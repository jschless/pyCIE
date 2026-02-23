"""Contract tests for scenario CLI execution and reporting."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pycie.cli import main


@pytest.fixture()
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "fixture_path",
    [
        "labs/scenarios/lab16_dual_failure.json",
        "labs/scenarios/lab16_single_link_failure.json",
    ],
)
def test_scenario_run_canonical_fixtures_pass(
    fixture_path: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
) -> None:
    monkeypatch.chdir(repo_root)
    code = main(["scenario", "run", fixture_path])

    out = capsys.readouterr().out
    assert code == 0
    assert ": PASS" in out


def test_scenario_run_returns_non_zero_on_failed_expectation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
) -> None:
    failing_scenario = tmp_path / "failing.json"
    failing_scenario.write_text(
        json.dumps(
            {
                "name": "failing-scenario",
                "lab_id": "lab16",
                "topology": {"nodes": ["r1"], "links": []},
                "actions": [],
                "expectations": [
                    {
                        "kind": "event_seen",
                        "selector": "fail_link",
                        "expected": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.chdir(repo_root)
    code = main(["scenario", "run", str(failing_scenario)])

    out = capsys.readouterr().out
    assert code == 1
    assert ": FAIL" in out
    assert "Failure details:" in out
    assert "selector='fail_link'" in out


def test_scenario_run_writes_json_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
) -> None:
    report = tmp_path / "scenario.json"

    monkeypatch.chdir(repo_root)
    code = main(
        [
            "scenario",
            "run",
            "labs/scenarios/lab16_dual_failure.json",
            "--report",
            "json",
            "--report-out",
            str(report),
        ]
    )

    out = capsys.readouterr().out
    assert code == 0
    assert "Report written:" in out
    assert report.exists()

    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["passed"] is True
    assert payload["lab_id"] == "lab16"
    assert payload["actions"] >= 1


def test_scenario_run_writes_markdown_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
) -> None:
    report = tmp_path / "scenario.md"

    monkeypatch.chdir(repo_root)
    code = main(
        [
            "scenario",
            "run",
            "labs/scenarios/lab16_single_link_failure.json",
            "--report",
            "md",
            "--report-out",
            str(report),
        ]
    )

    out = capsys.readouterr().out
    assert code == 0
    assert "Report written:" in out
    assert report.exists()

    text = report.read_text(encoding="utf-8")
    assert "# Scenario Report: single_link_failure_reconvergence" in text
    assert "- Status: `PASS`" in text
