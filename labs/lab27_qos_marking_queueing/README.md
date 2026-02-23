# Lab 27: QoS Marking and Queueing

## Goal

Implement deterministic QoS behavior: DSCP classification, policy remarking, queue admission, and weighted scheduling.

## Standards references

- DiffServ architecture: RFC 2475 — https://datatracker.ietf.org/doc/html/rfc2475
- DS field definition: RFC 2474 — https://datatracker.ietf.org/doc/html/rfc2474
- PHB examples: RFC 4594 — https://datatracker.ietf.org/doc/html/rfc4594

## Files to implement

- `src/pycie/protocols/qos_marking_queueing.py`
  - `QoSMarkingQueueingProcess.classify_dscp`
  - `QoSMarkingQueueingProcess.remark`
  - `QoSMarkingQueueingProcess.enqueue`
  - `QoSMarkingQueueingProcess.dequeue`
  - `QoSMarkingQueueingProcess.queue_depth`
  - `QoSMarkingQueueingProcess.snapshot_depths`

## Implementation hints

- Keep queue classification deterministic for every DSCP value.
- Enforce queue limits with explicit drop reason.
- Use weighted round-robin for bounded fairness.
- Ensure low-priority traffic is not starved under sustained priority load.

## Step-by-step implementation

1. Run tests once:

```bash
pytest -m "lab27 and exercise"
```

2. Implement DSCP classifier.
3. Implement remark and queue admission paths.
4. Implement weighted dequeue behavior.
5. Implement queue introspection helpers.
6. Re-run tests:

```bash
pytest -m "lab27 and exercise"
```

## Fast feedback commands

```bash
pytest tests/labs/test_lab27_qos_marking_queueing.py -q
pytest tests/labs/test_lab27_qos_marking_queueing_edge_cases.py -q
```

## Common mistakes

- Treating queue weights as strict priority forever.
- Not rotating scheduler cursor after credit exhaustion.
- Returning non-deterministic queue order under ties.

## Simplifications

- No hardware queue depth units or shaping.
- No RED/WRED drop algorithms.
- No per-flow hashing model.

## Tests

```bash
pytest -m "lab27 and exercise"
```

## Exit criteria

- Classification and queueing decisions are deterministic.
- Queue-full drop behavior is explicit.
- Best-effort traffic receives service under mixed load.
