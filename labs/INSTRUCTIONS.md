# Lab Instructions

This workbook is designed as a progression from foundational L2 forwarding to multi-protocol convergence and failure detection.

## How labs are structured

Each lab has:

1. Standards reading links.
2. Explicit implementation targets (function names).
3. Behavioral test suite markers.
4. Exit criteria (what must pass).

## Workflow per lab

1. Read the lab's standards notes.
2. Open the corresponding module under `src/pycie/protocols`.
3. Implement only the `TODO(student)` methods for that lab.
4. Run lab tests repeatedly.
5. Write short notes explaining state transitions and tie-breakers.

## Commands

Run base contract tests:

```bash
pytest
```

Run a single lab:

```bash
pytest -m "lab01 and exercise"
```

Run all lab tests:

```bash
pytest -m exercise
```

## Suggested pacing

1. Lab 01: 3-5 days
2. Lab 02: 4-6 days
3. Lab 03: 1-2 weeks
4. Lab 04: 1-2 weeks
5. Lab 05: 4-6 days
6. Lab 06: 3-5 days

## Completion standard

A lab is complete when:

1. All tests for that lab pass.
2. You can explain each state machine transition verbally.
3. You can explain at least one failure/reconvergence scenario from the lab.
