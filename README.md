# pyCIE

`pyCIE` is a protocol-first networking workbook scaffold.

The goal is to move from CCNA-level familiarity to CCIE-level protocol intuition by implementing protocol logic in Python and validating behavior with deterministic tests.

## What is included

- An event-driven network simulator scaffold.
- Core control-plane data model scaffolding (`RIB`, `FIB`, node/interface/link models).
- Data-plane model scaffolding for header stacks and encapsulation.
- Forwarding pipeline scaffolding (L2 VLAN bridge domain, ARP, IPv4, MPLS).
- Scenario DSL scaffolding for failure/reconvergence labs.
- Protocol module scaffolds for:
  - Learning switch
  - STP (simplified)
  - OSPF (simplified)
  - BGP (simplified)
  - LDP (simplified)
  - BFD (simplified)
  - ARP, RSTP, GRE, IPsec, policy, VRF, MPLS
- Lab instruction sheets in `/labs`.
- Capability matrix in `/labs/capabilities.json`.
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
pytest -m "lab01 and exercise"
```

Run all exercise tests:

```bash
pytest -m exercise
```

## Generate Student Scaffold

Generate a student TODO version of the codebase:

```bash
python tools/make_student_scaffold.py --input src/pycie --output dist/student/src/pycie --labs all
```

Generate a subset (example: lab07 and lab08 only):

```bash
python tools/make_student_scaffold.py --input src/pycie --output dist/student/src/pycie --labs lab07,lab08
```

## Documentation

- Architecture: [`/docs/architecture.md`](docs/architecture.md)
- Standards and RFC references: [`/docs/standards.md`](docs/standards.md)
- Full lab sequence and expectations: [`/labs/INSTRUCTIONS.md`](labs/INSTRUCTIONS.md)
- Capability matrix: [`/labs/capabilities.json`](labs/capabilities.json)
- Future lab roadmap: [`/docs/roadmap.md`](docs/roadmap.md)

## Design philosophy

- Keep scope narrow but behavior realistic.
- Implement protocol state machines and tie-breakers clearly.
- Test convergence, failures, and deterministic outcomes.
- Prioritize control-plane correctness over packet/wire fidelity.
