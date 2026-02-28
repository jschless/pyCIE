# Start Here

This is the shortest path from clone to meaningful learning.

<div class="link-grid">
  <a class="link-card" href="tutorial/">
    <strong>Continue to Tutorial</strong>
    Move from setup to chapter-by-chapter learning.
  </a>
  <a class="link-card" href="usage/">
    <strong>CLI Usage Guide</strong>
    Command reference and workflow patterns.
  </a>
  <a class="link-card" href="visualization/">
    <strong>Visualization Guide</strong>
    Trace capture and replay tools for debugging.
  </a>
</div>

## 1) Environment setup

```bash
git clone <repo-url>
cd pyCIE
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

Optional shortcut:

```bash
make bootstrap
```

If `pycie` is not on your shell path, run commands as:

```bash
python -m pycie <subcommand>
```

## 2) Confirm the install

```bash
pycie labs
pycie check
```

Expected result:

- `pycie labs` lists labs including `lab06a`, `lab06b`, `lab06c`
- New fundamentals/ops labs (`lab22`, `lab24`, `lab25`, `lab26`, `lab28`, `lab29`, `lab40`, `lab41`) are present
- `pycie check` passes contract tests

## 3) Start in student mode

`main` contains solved reference implementations. To work through TODO labs:

```bash
pycie scaffold --labs all
pycie run lab01 --student-src dist/student/src
```

If you choose in-place scaffold mode, you can restore solved source later:

```bash
pycie scaffold --labs all --in-place
pycie run lab01
pycie restore
```

## 4) First learning loop (30-45 minutes)

1. Implement one small lab:
   - `pycie run lab06a --student-src dist/student/src`
2. Run focused tests while iterating:
   - `pytest -m "lab06a and exercise"`
3. Capture and inspect telemetry:
   - `pycie run lab01 --student-src dist/student/src --trace-out traces/lab01.jsonl`
   - `pycie viz replay --trace traces/lab01.jsonl --detail packet`
   - `pycie viz explain --trace traces/lab01.jsonl --packet-id p1 --lab lab01`
   - `pycie viz web --trace traces/lab01.jsonl --out dist/viz/lab01 --lab lab01`

## 5) Follow the recommended sequence

Core sequence:

- `lab01` -> `lab02` -> `lab03` -> `lab04` -> `lab05` -> `lab06` -> `lab06a` -> `lab06b` -> `lab06c` -> `lab07` -> `lab22` -> `lab24` -> `lab25` -> `lab26` -> ...

Textbook flow with context and outcomes:

- [Tutorial Course Map](tutorial/index)
- [Pedagogical Lab Overview](labs/pedagogical_overview)

When you reach capstone labs, use this sequence for increasing scenario complexity:

- `pycie scenario validate labs/scenarios/lab16_single_link_failure.json`
- `pycie scenario run labs/scenarios/lab16_single_link_failure.json`
- `pycie scenario validate labs/scenarios/lab16_failure_recovery_drill.json`
- `pycie scenario run labs/scenarios/lab16_failure_recovery_drill.json`
- `pycie scenario validate labs/scenarios/lab16_dual_failure.json`
- `pycie scenario run labs/scenarios/lab16_dual_failure.json`

## Common pitfalls

- Running `pycie run lab01` before scaffolding and assuming labs are broken because tests pass immediately.
- Forgetting to activate `.venv`.
- Running plain `pytest` and expecting exercise labs (default config excludes `exercise`).

To run exercise suites explicitly:

```bash
pytest -m exercise
```

Useful shortcuts:

```bash
make check
make run-foundations
```
