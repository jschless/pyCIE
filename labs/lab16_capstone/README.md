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
