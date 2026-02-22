# Architecture

## Package map

- `src/pycie/sim`: simulation engine primitives
  - event queue
  - simulation clock
  - topology abstractions
- `src/pycie/core`: reusable control-plane models
  - node lifecycle hooks
  - `RIB` and `FIB` structures
- `src/pycie/protocols`: protocol scaffolds per lab
- `tests/contract`: shape and import guarantees
- `tests/labs`: behavior-driven lab tests

## Modeling approach

The simulator uses discrete events:

1. A protocol schedules timers/events.
2. Events execute in deterministic order `(time, priority, sequence)`.
3. Protocol handlers mutate local state and optionally schedule new events.

This gives repeatable convergence/failure behavior and allows strict unit testing.

## Test strategy

- Contract tests should always pass.
- Exercise tests are marked `exercise` and represent student tasks.
- Each lab is mapped to marker `lab01` through `lab06`.

## Scaffold conventions

- Methods students should implement use `NotImplementedError` with a `TODO(student)` message.
- Data classes and signatures are intentionally complete so students focus on logic, not structure.
- Protocol complexity is intentionally simplified where possible, but state-machine semantics are preserved.
