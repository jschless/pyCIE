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
        "labs/scenarios/lab16_failure_recovery_drill.json",
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


def test_scenario_validate_returns_zero_for_valid_fixture(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
) -> None:
    monkeypatch.chdir(repo_root)
    code = main(["scenario", "validate", "labs/scenarios/lab16_failure_recovery_drill.json"])

    out = capsys.readouterr().out
    assert code == 0
    assert ": VALID" in out
    assert "Actions=" in out
    assert "Expectations=" in out


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


def test_scenario_run_returns_argument_error_on_unknown_link_action(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
) -> None:
    invalid = tmp_path / "invalid-link.json"
    invalid.write_text(
        json.dumps(
            {
                "name": "invalid-link",
                "lab_id": "lab16",
                "topology": {"nodes": ["r1", "r2"], "links": [["r1:eth0", "r2:eth0"]]},
                "actions": [
                    {
                        "at_ms": 100,
                        "action": "fail_link",
                        "params": {"a": "r1:eth9", "b": "r2:eth9"},
                    }
                ],
                "expectations": [],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.chdir(repo_root)
    code = main(["scenario", "run", str(invalid)])

    err = capsys.readouterr().err
    assert code == 2
    assert "unknown endpoint" in err


def test_scenario_run_returns_argument_error_on_invalid_action_params(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
) -> None:
    invalid = tmp_path / "invalid-params.json"
    invalid.write_text(
        json.dumps(
            {
                "name": "invalid-params",
                "lab_id": "lab16",
                "topology": {"nodes": ["r1", "r2"], "links": [["r1:eth0", "r2:eth0"]]},
                "actions": [
                    {
                        "at_ms": 100,
                        "action": "fail_link",
                        "params": {"a": "r1:eth0"},
                    }
                ],
                "expectations": [],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.chdir(repo_root)
    code = main(["scenario", "run", str(invalid)])

    err = capsys.readouterr().err
    assert code == 2
    assert "actions[0].params.b must be a non-empty string" in err


def test_scenario_validate_returns_argument_error_on_invalid_schema(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repo_root: Path,
) -> None:
    invalid = tmp_path / "invalid-expectation.json"
    invalid.write_text(
        json.dumps(
            {
                "name": "invalid-expectation",
                "lab_id": "lab16",
                "topology": {"nodes": ["r1"], "links": []},
                "actions": [],
                "expectations": [
                    {
                        "kind": "convergence_ms_lte",
                        "selector": "fabric",
                        "expected": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.chdir(repo_root)
    code = main(["scenario", "validate", str(invalid)])

    err = capsys.readouterr().err
    assert code == 2
    assert "must be an integer" in err


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
    assert payload["action_timeline"]
    assert payload["action_timeline"][0]["timestamp_ms"] == "1000"
    assert payload["action_timeline"][0]["action"] == "fail_link"
    assert "key_state_change" in payload["action_timeline"][0]
    assert payload["telemetry"]["state"]["convergence"]["elapsed_ms"] > 0


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
    assert "## Action Timeline" in text
    assert "| timestamp_ms | action | key_state_change |" in text
    assert "`fail_link`" in text
