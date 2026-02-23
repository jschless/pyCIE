# Lab 13: BGP Policy and Route Attributes

## Goal

Implement route-policy matching and attribute mutation in import/export paths.

## Standards references

- RFC 4271 (BGP-4): https://datatracker.ietf.org/doc/html/rfc4271
- RFC 1997 (communities): https://datatracker.ietf.org/doc/html/rfc1997

## Files to implement

- `src/pycie/model/policy.py`
  - `RoutePolicy.evaluate`
  - `RoutePolicy.matches`
  - `RoutePolicy.apply_action`
- `src/pycie/protocols/policy.py`
  - `PolicyProcess.apply_import`
  - `PolicyProcess.apply_export`

## Implementation hints

- Keep route mutations side-effect safe:
  - copy input route dicts before modifying attributes.
- Policy rules should be evaluated in ascending `sequence` order.
- Use first-match behavior for a single policy evaluation.
- Explicitly model default behavior when no rule matches.
- Import/export chains should process policies in configured order and stop on deny.

## Step-by-step implementation plan

1. Run baseline tests:

```bash
pytest -m "lab13 and exercise"
```

2. Implement `RoutePolicy.matches`.
   - Evaluate each optional condition only when present.
   - Include AS-path length constraints.

3. Implement `RoutePolicy.apply_action`.
   - Apply local-pref, MED, AS-path prepend, and community mutation.
   - Preserve type consistency for `as_path`.

4. Implement `RoutePolicy.evaluate`.
   - Sort rules by sequence.
   - Return first matching rule result.
   - Handle no-match behavior deterministically.

5. Implement `PolicyProcess.apply_import` and `apply_export`.
   - Chain policies per neighbor.
   - Stop and return immediately on deny.

6. Re-run tests:

```bash
pytest -m "lab13 and exercise"
```

## Fast feedback commands

```bash
pytest tests/labs/test_lab13_bgp_policy.py -k permit_and_mutate -q
pytest tests/labs/test_lab13_bgp_policy.py -k applies_in_order -q
```

## Common mistakes

- Mutating caller-owned route objects in place.
- Ignoring rule sequence ordering.
- Continuing policy evaluation after a deny decision.
- Treating `as_path` as immutable tuple when prepend logic needs list behavior.

## Simplifications

- Prefix-list syntax is simplified to exact prefix matching initially.

## Tests

```bash
pytest -m "lab13 and exercise"
```

## Exit criteria

- Ordered policy rules are applied deterministically.
- Permit/deny and attribute mutation are both validated by tests.
