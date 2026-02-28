# Lab 16: Multi-Protocol Capstone

## Goal

Run scenario-driven convergence and resiliency exercises across L2/L3 protocols,
MPLS, and tunnels.

## Lab overview (what this is training)

This lab is not trying to emulate every router behavior in full fidelity.
It is training you to reason about network behavior as a deterministic sequence:

1. A disruption is injected at a known timestamp.
2. Observable state degrades in a specific way.
3. Recovery actions happen.
4. Convergence is measured and validated against expectations.

If earlier labs taught individual protocol mechanisms, this lab teaches
end-to-end reasoning across mechanisms. The key skill is turning "the network
is down" into explicit, testable state transitions and timing assertions.

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
- `labs/scenarios/lab16_failure_recovery_drill.json`
- `labs/scenarios/lab16_single_link_failure.json`
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
- Supported actions include:
  - `fail_link`
  - `recover_link`
  - `fail_bgp_peer`
  - `recover_bgp_peer`
  - `route_set_present`
  - `route_set_absent`
  - `mark_converged`
- `evaluate_expectation` should return `(ok, failure_message_or_none)` for each supported expectation kind.
- Keep failure messages specific enough for learners to debug expectation mismatches.
- Scenario files are schema-validated before execution:
  - unsupported actions/expectations fail at load time
  - required action params are enforced per action type
  - expectation `expected` types are validated by expectation kind

## Scenario timeline semantics

When reading or writing a scenario fixture, each action should map to a
teaching purpose:

1. `fail_link` / `fail_bgp_peer`
   - Introduce explicit fault domains.
   - Start convergence timing window.
2. `route_set_absent`
   - Make impact observable in route state.
3. `recover_link` / `recover_bgp_peer`
   - Model restoration actions independently from failure injection.
4. `route_set_present`
   - Represent successful control-plane recovery.
5. `mark_converged`
   - Define when the scenario considers the system stable.

Use this pattern to avoid "magic convergence." Every major behavior change
should appear as a timestamped action or expectation.

## Step-by-step implementation plan

1. Run capstone tests:

```bash
pytest -m "lab16 and exercise"
```

2. Run canonical fixtures to understand target behavior:

```bash
pycie scenario validate labs/scenarios/lab16_single_link_failure.json
pycie scenario run labs/scenarios/lab16_single_link_failure.json --report md
pycie scenario validate labs/scenarios/lab16_failure_recovery_drill.json
pycie scenario run labs/scenarios/lab16_failure_recovery_drill.json --report md
```

3. Implement `apply_action`.
   - Normalize action enum/string.
   - Record event payload (include `_at_ms`).
   - Update topology, BGP peer, and route state for each action.
   - Validate referenced nodes/endpoints so bad scenarios fail fast.

4. Implement `evaluate_expectation`.
   - Support event presence checks.
   - Support convergence threshold checks from first disruption to explicit convergence mark.
   - Support route-presence checks from scenario route state.
   - Return useful mismatch messages.

5. Implement `run`.
   - Validate lab capability availability.
   - Execute actions sorted by timestamp.
   - Evaluate all expectations and build `ScenarioResult`.

6. Validate against provided scenario artifacts to ensure field names/IDs line up.

7. Re-run tests:

```bash
pytest -m "lab16 and exercise"
```

## Fast feedback commands

```bash
pycie scenario validate labs/scenarios/lab16_failure_recovery_drill.json
pytest tests/labs/test_lab16_capstone.py -k executes_actions -q
pytest -m "lab16 and exercise" -q
pycie scenario run labs/scenarios/lab16_failure_recovery_drill.json --report json
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
- Failure and recovery behavior is repeatable.
- Scenario artifacts can express both disruption and restoration workflows clearly.
