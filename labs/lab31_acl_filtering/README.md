# Lab 31: ACL Filtering

## Goal

Implement ordered ACL rule evaluation with first-match semantics and implicit deny.

## Standards references

- IPv4 forwarding/filtering requirements: RFC 1812 — https://datatracker.ietf.org/doc/html/rfc1812

## Files to implement

- `src/pycie/protocols/acl.py`
  - `ACLRule.matches`
  - `ACL.add_rule`
  - `ACL.remove_rule`
  - `ACL.evaluate`

## Step-by-step implementation

1. Implement packet/rule field matching.
2. Add sequence-based ordering and replacement behavior.
3. Implement first-match action return.
4. Enforce implicit deny when no rules match.
5. Run tests: `pytest -m "lab31 and exercise"`.

## Advanced extensions

- Add wildcard-mask style matching syntax.
- Add object-group style abstractions.
- Add logging counters for hit statistics.

## Simplifications

- No hardware TCAM limits.
- No reflexive/stateful ACL model.

## Tests

```bash
pytest -m "lab31 and exercise"
```

## Exit criteria

- Rule order deterministically controls behavior.
- Implicit deny always applies.
- Protocol and port conditions are respected.
