# Lab Instructions

This workbook is designed as a progression from foundational L2 forwarding to multi-protocol convergence and failure detection.

The first six labs focus on core control-plane behavior. Labs 07+ extend into full data-plane modeling, encapsulation, policy, VRF, and capstone failure scenarios.

## How labs are structured

Each lab has:

1. Standards reading links.
2. Explicit implementation targets (function names).
3. Behavioral test suite markers.
4. Exit criteria (what must pass).

## Workflow per lab

1. Read the lab's standards notes.
2. Open the corresponding module under `src/pycie/protocols`.
3. If the lab includes data-plane work, also implement modules under `src/pycie/forwarding` and `src/pycie/model`.
4. Implement only the `TODO(student)` methods for that lab.
5. Confirm feature scope in `labs/capabilities.json`.
6. Run lab tests repeatedly.
7. Write short notes explaining state transitions and tie-breakers.

## Scaffold API Quick Reference

Use these helpers when implementing protocol methods:

- `self.device.interfaces`
  - A `dict[str, Interface]` of local interfaces keyed by interface name.
  - Example keys: `eth0`, `eth1`.
- `self.now_ms`
  - Current simulation time in milliseconds.
  - Useful for aging and timer-based state.
- `self.device.send_frame(egress_if, frame)`
  - Sends a frame out a local interface name.
- `frame.src_mac`, `frame.dst_mac`, `frame.ethertype`, `frame.payload`
  - Fields on incoming `Frame` objects.
- `self.node_id`
  - Local device ID shortcut.

Useful iteration patterns:

```python
for if_name in sorted(self.device.interfaces):
    ...
```

```python
for if_name, interface in self.device.interfaces.items():
    ...
```

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

Run a scenario-driven capstone suite (when implemented):

```bash
pytest -m "lab16 and exercise"
```

Generate a student scaffold from reference code:

```bash
python tools/make_student_scaffold.py --input src/pycie --output dist/student/src/pycie --labs all
```

Run tests against scaffold output (instead of reference source):

```bash
PYCIE_SRC=dist/student/src pytest -m "lab01 and exercise"
```

## Suggested pacing

1. Lab 01: 3-5 days
2. Lab 02: 4-6 days
3. Lab 03: 1-2 weeks
4. Lab 04: 1-2 weeks
5. Lab 05: 4-6 days
6. Lab 06: 3-5 days
7. Lab 07: 3-5 days
8. Lab 08: 3-4 days
9. Lab 09: 4-6 days
10. Lab 10: 4-6 days
11. Lab 11: 3-5 days
12. Lab 12: 5-8 days
13. Lab 13: 4-6 days
14. Lab 14: 5-8 days
15. Lab 15: 4-7 days
16. Lab 16: 1-2 weeks

## Completion standard

A lab is complete when:

1. All tests for that lab pass.
2. You can explain each state machine transition verbally.
3. You can explain at least one failure/reconvergence scenario from the lab.
