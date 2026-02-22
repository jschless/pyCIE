# pyCIE

`pyCIE` is a protocol-first networking workbook scaffold.

The goal is to move from CCNA-level familiarity to CCIE-level protocol intuition by implementing protocol logic in Python and validating behavior with deterministic tests.

## What is included

- An event-driven network simulator scaffold.
- Core control-plane data model scaffolding (`RIB`, `FIB`, node/interface/link models).
- Protocol module scaffolds for:
  - Learning switch
  - STP (simplified)
  - OSPF (simplified)
  - BGP (simplified)
  - LDP (simplified)
  - BFD (simplified)
- Lab instruction sheets in `/labs`.
- A test suite split into:
  - Contract tests (pass now)
  - Exercise tests (run during each lab)

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Run tests

Default test run (contract checks only):

```bash
pytest
```

Run a specific lab test set:

```bash
pytest -m lab01 -m exercise
```

Run all exercise tests:

```bash
pytest -m exercise
```

## Documentation

- Architecture: [`/docs/architecture.md`](docs/architecture.md)
- Standards and RFC references: [`/docs/standards.md`](docs/standards.md)
- Full lab sequence and expectations: [`/labs/INSTRUCTIONS.md`](labs/INSTRUCTIONS.md)

## Design philosophy

- Keep scope narrow but behavior realistic.
- Implement protocol state machines and tie-breakers clearly.
- Test convergence, failures, and deterministic outcomes.
- Prioritize control-plane correctness over packet/wire fidelity.
