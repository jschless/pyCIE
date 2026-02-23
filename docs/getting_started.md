# Start Here

This is the shortest path from clone to meaningful learning.

## 1) Environment setup

```bash
git clone <repo-url>
cd pyCIE
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
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
- `pycie check` passes contract tests

## 3) Start in student mode

`main` contains solved reference implementations. To work through TODO labs:

```bash
pycie scaffold --labs all
pycie run lab01
```

You can restore solved source later:

```bash
pycie restore
```

## 4) First learning loop (30-45 minutes)

1. Implement one small lab:
   - `pycie run lab06a`
2. Run focused tests while iterating:
   - `pytest -m "lab06a and exercise"`
3. Capture and inspect telemetry:
   - `pycie run lab01 --trace-out traces/lab01.jsonl`
   - `pycie viz replay --trace traces/lab01.jsonl --detail packet`

## 5) Follow the recommended sequence

Core sequence:

- `lab01` -> `lab02` -> `lab03` -> `lab04` -> `lab05` -> `lab06` -> `lab06a` -> `lab06b` -> `lab06c` -> `lab07` -> ...

Textbook flow with context and outcomes:

- [Tutorial Course Map](tutorial/index.md)

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
