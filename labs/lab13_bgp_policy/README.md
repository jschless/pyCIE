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

## Simplifications

- Prefix-list syntax is simplified to exact prefix matching initially.

## Tests

```bash
pytest -m "lab13 and exercise"
```

## Exit criteria

- Ordered policy rules are applied deterministically.
- Permit/deny and attribute mutation are both validated by tests.
