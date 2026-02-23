# Usage Guide

This guide is for software engineers using pyCIE to build networking protocol intuition through code.

## What pyCIE is

pyCIE is a protocol-first networking workbook.

- You learn by implementing protocol behavior in Python.
- You validate your understanding with deterministic tests.
- You can study labs in sequence or run a focused topic lab.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

If the `pycie` command is not on your path, use module mode:

```bash
python -m pycie <subcommand>
```

## CLI Quickstart

Show first-run steps:

```bash
pycie quickstart
```

List labs:

```bash
pycie labs
```

Show one lab:

```bash
pycie show lab01
```

Run one lab:

```bash
pycie run lab01
```

Generate TODO scaffold from reference source:

```bash
pycie scaffold --labs all
```

Run one lab:

```bash
pycie run lab01
```

Restore solved source after scaffolding:

```bash
pycie restore
pycie restore --labs lab01,lab07
```

Optional out-of-tree scaffold workflow:

```bash
pycie scaffold --labs all --output dist/student/src/pycie
pycie run lab01 --student-src dist/student/src
```

Run one lab and capture telemetry:

```bash
pycie run lab01 --trace-out traces/lab01.jsonl
```

Run all exercise labs:

```bash
pycie run all
```

Run contract checks only:

```bash
pycie check
```

Show doc map:

```bash
pycie guide
```

Trace replay commands:

```bash
pycie viz replay --trace traces/lab01.jsonl --detail packet
pycie viz packet --trace traces/lab01.jsonl --packet-id p1 --detail full
pycie viz topology --trace traces/lab01.jsonl --packet-id p1
pycie viz sequence --trace traces/lab01.jsonl --packet-id p1 --detail packet
pycie viz stp --trace traces/lab02.jsonl
```

## Recommended learning paths

### Core protocol sequence

1. `lab01` through `lab16`
2. Then advanced labs (`lab23`, `lab30+`)

### Router decision internals

1. `lab23_isis`
2. `lab38_control_plane_databases`
3. `lab30_route_selection_redistribution`
4. `lab39_rib_to_fib_pipeline`

### Services/security track

1. `lab31_acl_filtering`
2. `lab33_dhcp_services`
3. `lab32_aaa_access_control`
4. `lab37_macsec_link_security`

### Overlay/multicast track

1. `lab34_multicast_foundations`
2. `lab35_vxlan_overlay_data_plane`
3. `lab36_evpn_control_plane`

## Student workflow options

### Option A: Branch-based workflow (recommended)

1. Create a branch from `main`.
2. Implement TODO logic directly in source modules.
3. Run `pycie run <labXX>` until green.

### Option B: Scaffold workflow

Generate student TODO scaffold:

```bash
pycie scaffold --labs all
```

Run tests directly:

```bash
pycie run lab01
```

### Fresh clone behavior

`main` ships with reference solutions. If you run `pycie run lab01` directly in a fresh clone, tests run against solved source.
To force TODO-based student work, run `pycie scaffold --labs all` first.
By default, this writes TODO scaffolding into `src/pycie` and snapshots solved code to `dist/reference/src/pycie`.

Restore solved source any time:

```bash
pycie restore
```

Restore only selected labs:

```bash
pycie restore --labs lab01,lab07
```

## Repo map

- `src/pycie/sim`: event-driven simulation primitives
- `src/pycie/core`: device, RIB/FIB core models
- `src/pycie/model`: headers, packet stack, capabilities
- `src/pycie/forwarding`: L2/L3/MPLS/encapsulation behaviors
- `src/pycie/protocols`: per-lab protocol logic
- `tests/contract`: baseline shape/sanity tests
- `tests/labs`: lab behavior tests
- `labs`: lab READMEs and capability matrix

## Troubleshooting

### Unknown lab ID in CLI

Use `pycie labs` to list valid IDs and exact names.

### No tests discovered

Remember exercise tests are marker-filtered. Use `pycie run <labXX>` or:

```bash
pytest -m "labXX and exercise"
```

### CLI command missing

Use module mode:

```bash
python -m pycie labs
```

## Next docs

- Architecture: `docs/architecture.md`
- Standards: `docs/standards.md`
- Visualization: `docs/visualization.md`
- Lab instructions: `labs/INSTRUCTIONS.md`
- Roadmap: `docs/roadmap.md`
- Product TODO: `docs/TODO.md`
