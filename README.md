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
pycie run lab01
```

If `pycie` is not on path:

```bash
python -m pycie labs
```

## CLI commands

- `pycie labs`: list available labs and README paths
- `pycie show <labXX>`: show details for one lab
- `pycie run <labXX>`: run one lab's exercise tests
- `pycie run all`: run all exercise tests
- `pycie check`: run contract tests only
- `pycie guide`: print key docs and recommended commands
- `pycie quickstart`: print first-run setup steps

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

Run all exercise labs:

```bash
pytest -m exercise
```

## Learning paths

### Foundational path

- `lab01` through `lab16`

### Router internals path

- `lab23` -> `lab38` -> `lab30` -> `lab39`

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
python tools/make_student_scaffold.py --input src/pycie --output dist/student/src/pycie --labs all
PYCIE_SRC=dist/student/src pytest -m "lab01 and exercise"
```

## Documentation

- Usage guide: [`docs/usage.md`](docs/usage.md)
- Full lab instructions: [`labs/INSTRUCTIONS.md`](labs/INSTRUCTIONS.md)
- Architecture: [`docs/architecture.md`](docs/architecture.md)
- Standards references: [`docs/standards.md`](docs/standards.md)
- Roadmap/backlog: [`docs/roadmap.md`](docs/roadmap.md)
- Product TODO: [`docs/TODO.md`](docs/TODO.md)
