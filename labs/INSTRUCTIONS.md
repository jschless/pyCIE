# Lab Instructions

This workbook is designed as a progression from foundational L2 forwarding to multi-protocol convergence and failure detection.

The first six labs focus on core control-plane behavior.
Labs `06a`-`06c` add packet/transport/addressing fundamentals before `lab07`.
Labs `22`, `24`, `25`, `26`, `28`, `29`, `40`, and `41` extend fundamentals into diagnostics, MTU behavior, host services, and operations.
Labs `07+` extend into full data-plane modeling, encapsulation, policy, VRF, and capstone failure scenarios.

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

## Step Intent (How to think about each TODO)

Each TODO method is not just "code to make tests pass." It represents one stage in
protocol reasoning. Use this sequence while implementing:

1. Input and state validation
   - Confirm packet fields, timers, and identifiers are admissible.
   - Reject malformed or out-of-scope input early and explicitly.
2. Candidate construction
   - Build the possible outputs (ports, routes, sessions, policies, labels).
   - Keep candidates explicit so tie-break logic is visible.
3. Deterministic decision
   - Apply documented ranking/tie-break rules in fixed order.
   - Preserve deterministic behavior for reproducible tests.
4. State commit
   - Update local tables/state machines only after a decision is made.
   - Keep transitions explainable ("from X to Y because Z").
5. Output action and reason
   - Forward/flood/advertise/drop with a clear reason.
   - Prefer explicit drop reasons so behavior is debuggable.
6. Aging and recovery
   - Handle timeout expiration and reconvergence as first-class behavior.

Deep lab-by-lab pedagogical context:

- `docs/labs/pedagogical_overview.md`

## Capstone lens (`lab16`)

In `lab16`, treat each scenario action as a concrete implementation step in an
incident timeline:

1. Disruptions:
   - `fail_link`, `fail_bgp_peer`
2. Observable impact:
   - `route_set_absent`
3. Restorations:
   - `recover_link`, `recover_bgp_peer`
4. Recovery completion:
   - `route_set_present`, `mark_converged`

When implementing runner behavior, ask:

1. What state changed?
2. Is the state change timestamped and reproducible?
3. What expectation proves the behavior happened?

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
7. Lab 06a: 2-4 days
8. Lab 06b: 3-5 days
9. Lab 06c: 3-5 days
10. Lab 07: 3-5 days
11. Lab 08: 3-4 days
12. Lab 09: 4-6 days
13. Lab 10: 4-6 days
14. Lab 11: 3-5 days
15. Lab 12: 5-8 days
16. Lab 13: 4-6 days
17. Lab 14: 5-8 days
18. Lab 15: 4-7 days
19. Lab 16: 1-2 weeks

For post-capstone labs (`lab17+`), use the same pacing model:

1. Start with 3-5 days for service/security labs (`lab19`, `lab31`-`lab33`, `lab37`).
2. Use 4-7 days for control-plane labs (`lab17`, `lab18`, `lab20`, `lab23`, `lab34`, `lab36`, `lab38`).
3. Use 3-5 days for QoS/policy labs (`lab27`, `lab31`).
4. Use 5-8 days for pipeline/overlay labs (`lab21`, `lab30`, `lab35`, `lab39`).

## Completion standard

A lab is complete when:

1. All tests for that lab pass.
2. You can explain each state machine transition verbally.
3. You can explain at least one failure/reconvergence scenario from the lab.
