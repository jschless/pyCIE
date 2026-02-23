# Lab Instructions

This workbook is designed as a progression from foundational L2 forwarding to multi-protocol convergence and failure detection.

The first six labs focus on core control-plane behavior. Labs 07+ extend into full data-plane modeling, encapsulation, policy, VRF, and capstone failure scenarios.

Use `/docs/roadmap.md` as the active backlog for realism upgrades and new labs (`lab17+`).

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
pycie check
pytest
```

Run a single lab:

```bash
pycie run lab01
pytest -m "lab01 and exercise"
```

Run a lab with trace capture:

```bash
pycie run lab01 --trace-out traces/lab01.jsonl
```

Replay and inspect trace output:

```bash
pycie viz replay --trace traces/lab01.jsonl
pycie viz packet --trace traces/lab01.jsonl --packet-id p1
pycie viz stp --trace traces/lab02.jsonl
```

Run all lab tests:

```bash
pycie run all
pytest -m exercise
```

Run any extended lab (example: lab33):

```bash
pytest -m "lab33 and exercise"
```

Run a scenario-driven capstone suite (when implemented):

```bash
pytest -m "lab16 and exercise"
```

Generate a student scaffold from reference code:

```bash
pycie scaffold --labs all
```

Run tests against scaffold output (instead of reference source):

```bash
pycie run lab01 --student-src dist/student/src
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

For post-capstone labs (`lab17+`), use the same pacing model:

1. Start with 3-5 days for service/security labs (`lab31`-`lab33`, `lab37`).
2. Use 4-7 days for control-plane labs (`lab17`, `lab18`, `lab23`, `lab34`, `lab36`, `lab38`).
3. Use 5-8 days for pipeline/overlay labs (`lab30`, `lab35`, `lab39`).

## Completion standard

A lab is complete when:

1. All tests for that lab pass.
2. You can explain each state machine transition verbally.
3. You can explain at least one failure/reconvergence scenario from the lab.
