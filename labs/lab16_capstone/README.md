# Lab 16: Multi-Protocol Capstone

## Goal

Run a scenario-driven convergence and resiliency exercise across L2/L3 protocols, MPLS, and tunnels.

## Standards references

- RFC 2328, RFC 4271, RFC 5036, RFC 5880
- RFC 2784, RFC 4301
- RFC 4364

## Files to implement

- `src/pycie/scenario/runner.py`
  - `ScenarioRunner.run`
  - `ScenarioRunner.apply_action`
  - `ScenarioRunner.evaluate_expectation`
- Any unresolved protocol/forwarding TODOs required by selected scenario.

## Input artifacts

- `labs/scenarios/lab16_dual_failure.json`
- `labs/capabilities.json`

## Implementation hints

- `ScenarioRunner.run` is the orchestration entrypoint:
  - validate capability set for scenario lab ID
  - execute actions in time order
  - evaluate expectations and summarize failures
- Keep internal telemetry structures explicit and stable:
  - event log list
  - state dict for action effects
- `apply_action` should normalize action type and record each event consistently.
- `evaluate_expectation` should return `(ok, failure_message_or_none)` for each supported expectation kind.
- Keep failure messages specific enough for learners to debug expectation mismatches.

## Step-by-step implementation plan

1. Run capstone tests:

```bash
pytest -m "lab16 and exercise"
```

2. Implement `apply_action`.
   - Normalize action enum/string.
   - Record event payload.
   - Update minimal scenario state hooks for supported actions.

3. Implement `evaluate_expectation`.
   - Support event presence checks.
   - Support convergence threshold checks in the simplified model.
   - Support route-presence placeholder checks.
   - Return useful mismatch messages.

4. Implement `run`.
   - Validate lab capability availability.
   - Execute actions sorted by timestamp.
   - Evaluate all expectations and build `ScenarioResult`.

5. Validate against provided scenario artifacts to ensure field names/IDs line up.

6. Re-run tests:

```bash
pytest -m "lab16 and exercise"
```

## Fast feedback commands

```bash
pytest tests/labs/test_lab16_capstone.py -k executes_actions -q
pytest -m "lab16 and exercise" -q
```

## Common mistakes

- Executing scenario actions in declaration order instead of timestamp order.
- Recording events with inconsistent action identifiers.
- Returning only booleans from expectation checks and losing failure detail.
- Skipping capability validation for unknown/disabled labs.

## Simplifications

- Telemetry checks are logical assertions, not raw pcap validation.

## Tests

```bash
pytest -m "lab16 and exercise"
```

## Exit criteria

- Scenario actions execute in time order.
- Expectations are evaluated and clearly reported.
- Failure/recovery behavior is repeatable.
