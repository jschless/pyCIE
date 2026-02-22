# Architecture

## Package map

- `src/pycie/sim`: simulation engine primitives
  - event queue
  - simulation clock
  - topology abstractions
- `src/pycie/core`: reusable control-plane models
  - node lifecycle hooks
  - `RIB` and `FIB` structures
- `src/pycie/model`: packet/header/policy/capability data models
  - encapsulation stack headers (Ethernet, 802.1Q, IPv4, GRE, ESP, MPLS)
  - lab capability matrix representation
  - route-policy data structures
- `src/pycie/forwarding`: data-plane forwarding pipelines
  - VLAN-aware L2 bridge behavior
  - ARP cache and pending queue
  - IPv4 longest-prefix forwarding
  - encapsulation/decapsulation helpers
  - MPLS LFIB forwarding helpers
- `src/pycie/protocols`: protocol scaffolds per lab
- `src/pycie/scenario`: scenario DSL and runner scaffolding
- `tests/contract`: shape and import guarantees
- `tests/labs`: behavior-driven lab tests

## Separation of concerns

The codebase is organized to scale complexity safely:

1. `sim` controls time and event ordering only.
2. `model` defines immutable-ish protocol and packet structures.
3. `forwarding` executes data-plane decisions.
4. `protocols` computes control-plane state and desired forwarding outputs.
5. `scenario` drives end-to-end convergence and failure exercises.

## Modeling approach

The simulator uses discrete events:

1. A protocol schedules timers/events.
2. Events execute in deterministic order `(time, priority, sequence)`.
3. Protocol handlers mutate local state and optionally schedule new events.

This gives repeatable convergence/failure behavior and allows strict unit testing.

## Capability gating

`labs/capabilities.json` is the source of truth for which features are enabled per lab.

- Tests and scenario runs should only validate capabilities enabled for that lab.
- This prevents early labs from inheriting hidden complexity from later features.

## Test strategy

- Contract tests should always pass.
- Exercise tests are marked `exercise` and represent student tasks.
- Each lab is mapped to a marker (`lab01`, `lab02`, ..., advanced lab IDs).

## Scaffold conventions

- Methods students should implement use `NotImplementedError` with a `TODO(student)` message.
- Data classes and signatures are intentionally complete so students focus on logic, not structure.
- Protocol complexity is intentionally simplified where possible, but state-machine semantics are preserved.
