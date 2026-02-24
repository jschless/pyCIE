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
pip install -e '.[dev]'
```

Shortcut:

```bash
make bootstrap
```

If the `pycie` command is not on your path, use module mode:

```bash
python -m pycie <subcommand>
```

For first-time onboarding, use:

- [`docs/getting_started.md`](getting_started)
- [`docs/tutorial/index.md`](tutorial/index)

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
pycie run lab01 --student-src dist/student/src
pycie run lab06a --student-src dist/student/src
pycie run lab06b --student-src dist/student/src
pycie run lab06c --student-src dist/student/src
```

Generate TODO scaffold from reference source:

```bash
pycie scaffold --labs all
```

Run one lab:

```bash
pycie run lab01 --student-src dist/student/src
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
pycie run lab01 --student-src dist/student/src --trace-out traces/lab01.jsonl
```

Run all exercise labs:

```bash
pycie run all --student-src dist/student/src
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
pycie viz web --trace traces/lab01.jsonl --out dist/viz/lab01
pycie scenario run labs/scenarios/lab16_dual_failure.json --report json --report-out dist/reports/lab16.json
```

## Recommended learning paths

### Core protocol sequence

1. `lab01` -> `lab02` -> `lab03` -> `lab04` -> `lab05` -> `lab06` -> `lab06a` -> `lab06b` -> `lab06c` -> `lab07` -> ... -> `lab21`
2. Continue with fundamentals depth: `lab22`, `lab24`, `lab25`, `lab26`, `lab29`
3. Then advanced labs (`lab23`, `lab30+`, `lab40`, `lab41`)

### Router decision internals

1. `lab06c_ip_subnet_mac_forwarding_basics`
2. `lab17_bgp_fsm_transport`
3. `lab18_ospf_multi_area`
4. `lab19_ikev2_for_ipsec`
5. `lab20_ipv6_nd_forwarding`
6. `lab21_nat44_pipeline`
7. `lab23_isis`
8. `lab38_control_plane_databases`
9. `lab30_route_selection_redistribution`
10. `lab39_rib_to_fib_pipeline`

### QoS and policy track

1. `lab06b_tcp_udp_fundamentals`
2. `lab06c_ip_subnet_mac_forwarding_basics`
3. `lab13_bgp_policy`
4. `lab27_qos_marking_queueing`
5. `lab31_acl_filtering`

### Services/security track

1. `lab31_acl_filtering`
2. `lab28_dhcpv6_services`
3. `lab33_dhcp_services`
4. `lab32_aaa_access_control`
5. `lab40_fhrp_gateway_redundancy`
6. `lab41_management_plane_observability`
7. `lab37_macsec_link_security`

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
pycie run lab01 --student-src dist/student/src
```

### Fresh clone behavior

`main` ships with reference solutions. If you run `pycie run lab01` directly in a fresh clone, tests run against solved source.
To force TODO-based student work, run `pycie scaffold --labs all` first.
By default, this writes TODO scaffolding into `dist/student/src/pycie`.

For in-place mode, use explicit opt-in and then restore from snapshot later:

```bash
pycie scaffold --labs all --in-place
pycie run lab01
```

Restore solved source any time (in-place mode only):

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

- Start here: `docs/getting_started.md`
- Textbook tutorial: `docs/tutorial/index.md`
- Docs site workflow: `docs/docs_site.md`
- Architecture: `docs/architecture.md`
- Standards: `docs/standards.md`
- Visualization: `docs/visualization.md`
- Lab instructions: `labs/INSTRUCTIONS.md`
- Roadmap: `docs/roadmap.md`
- Product TODO: `docs/TODO.md`

## Build docs site locally

```bash
pip install -e '.[docs]'
sphinx-autobuild docs docs/_build/dirhtml
sphinx-build -W -b dirhtml docs docs/_build/dirhtml
```
