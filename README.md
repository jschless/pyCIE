# pyCIE

`pyCIE` is a networking protocol workbook for software engineers.

You learn networking by implementing protocol logic in Python, not by memorizing vendor CLI commands.

## Who this is for

- Software engineers who want deep protocol intuition.
- Network engineers who want to reason in code.
- Anyone moving from CCNA-level familiarity toward CCNP/CCIE-level understanding.

## What you do in this repo

- Implement protocol state machines and forwarding logic.
- Run deterministic lab tests.
- Study failure and reconvergence behavior.
- Build understanding incrementally from L2 switching to overlays and control-plane internals.

## Why this approach works

- You can inspect every decision point in code.
- Tests force precise behavior and edge-case handling.
- Labs are modular: follow the sequence or pick topic tracks.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

Then use the CLI:

```bash
pycie quickstart
pycie labs
pycie scaffold --labs all
pycie run lab01
pycie run lab01 --trace-out traces/lab01.jsonl
pycie viz replay --trace traces/lab01.jsonl --detail packet
pycie viz topology --trace traces/lab01.jsonl --packet-id p1
pycie viz sequence --trace traces/lab01.jsonl --packet-id p1 --detail packet
pycie viz web --trace traces/lab01.jsonl --out dist/viz/lab01
pycie scenario run labs/scenarios/lab16_dual_failure.json
```

If `pycie` is not on path:

```bash
python -m pycie labs
```

## CLI commands

- `pycie labs`: list available labs and README paths
- `pycie show <labXX>`: show details for one lab
- `pycie run <labXX>`: run one lab's exercise tests
- `pycie run <labXX> --trace-out <file>`: run lab and capture telemetry JSONL
- `pycie run all`: run all exercise tests
- `pycie scaffold --labs <list|all>`: apply TODO scaffold to `src/pycie` (in place) by default
- `pycie restore`: restore solved source from `dist/reference/src/pycie`
- `pycie restore --labs <list>`: restore solved files for specific labs only
- `pycie run <labXX> --student-src <dir>`: optional alternate source root for advanced workflows
- `pycie check`: run contract tests only
- `pycie guide`: print key docs and recommended commands
- `pycie quickstart`: print first-run setup steps
- `pycie viz replay --trace <file>`: replay trace timeline
- `pycie viz packet --trace <file> --packet-id <id>`: packet life-of-flow view
- `pycie viz topology --trace <file>`: topology snapshot + packet position
- `pycie viz sequence --trace <file>`: grouped playback over simulation time
- `pycie viz stp --trace <file>`: STP election/role summary
- `pycie viz web --trace <file> --out <dir>`: generate an offline HTML viewer
- `pycie scenario run <scenario-file>`: run a scenario fixture with pass/fail exit status

## Lab model

Each lab provides:

1. Standards/RFC links.
2. Target files and methods.
3. Step-by-step implementation guidance.
4. Advanced extension ideas.
5. Deterministic exercise tests.

Run one lab manually:

```bash
pytest -m "lab01 and exercise"
```

Capture trace while running one lab:

```bash
pycie run lab01 --trace-out traces/lab01.jsonl
pycie viz replay --trace traces/lab01.jsonl
pycie viz web --trace traces/lab01.jsonl --out dist/viz/lab01
pycie scenario run labs/scenarios/lab16_dual_failure.json --report md --report-out dist/reports/lab16.md
```

Run all exercise labs:

```bash
pytest -m exercise
```

## Learning paths

### Foundational path

- `lab01` through `lab18`

### Router internals path

- `lab17` -> `lab18` -> `lab23` -> `lab38` -> `lab30` -> `lab39`

### Services/security path

- `lab31` -> `lab33` -> `lab32` -> `lab37`

### Overlay/multicast path

- `lab34` -> `lab35` -> `lab36`

## Repository structure

- `src/pycie/sim`: simulation primitives
- `src/pycie/core`: device lifecycle and RIB/FIB models
- `src/pycie/model`: packet/header/capability models
- `src/pycie/forwarding`: L2/L3/MPLS/encapsulation behaviors
- `src/pycie/protocols`: protocol modules by lab
- `tests/contract`: baseline contract checks
- `tests/labs`: lab behavior tests
- `labs`: lab instructions and capability matrix
- `docs`: architecture, standards, roadmap, TODO

## Student workflow

### Branch-based workflow (recommended)

1. Create a branch from `main`.
2. Implement TODO logic in source files.
3. Run `pycie run <labXX>` repeatedly.

### Scaffold workflow

```bash
pycie scaffold --labs all
pycie run lab01
pycie restore
```

### Fresh-clone student mode (blank labs)

`main` includes the reference implementation, so `pycie run lab01` will pass immediately against solved code.
If you want blank TODO labs after cloning:

```bash
pycie scaffold --labs all
pycie run lab01
```

This snapshots solved code to `dist/reference/src/pycie` automatically, so you can restore later:

```bash
pycie restore
pycie restore --labs lab01,lab07
```

Optional out-of-tree scaffold:

```bash
pycie scaffold --labs all --output dist/student/src/pycie
pycie run lab01 --student-src dist/student/src
```

Optional isolation:

```bash
git checkout -b student/<name>
```

## Documentation

- Usage guide: [`docs/usage.md`](docs/usage.md)
- Visualization guide: [`docs/visualization.md`](docs/visualization.md)
- Full lab instructions: [`labs/INSTRUCTIONS.md`](labs/INSTRUCTIONS.md)
- Architecture: [`docs/architecture.md`](docs/architecture.md)
- Standards references: [`docs/standards.md`](docs/standards.md)
- Roadmap/backlog: [`docs/roadmap.md`](docs/roadmap.md)
- Product TODO: [`docs/TODO.md`](docs/TODO.md)
