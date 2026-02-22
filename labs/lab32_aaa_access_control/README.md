# Lab 32: AAA Access Control

## Goal

Implement backend/local authentication flow, role-based authorization, and accounting records.

## Standards references

- RADIUS: RFC 2865 — https://datatracker.ietf.org/doc/html/rfc2865
- TACACS+: RFC 8907 — https://datatracker.ietf.org/doc/html/rfc8907

## Files to implement

- `src/pycie/protocols/aaa.py`
  - `AAAService.login`
  - `AAAService.authorize`
  - `AAAService.logout`
  - `AAAService._authenticate_backend`
  - `AAAService._record`

## Step-by-step implementation

1. Implement local-user authentication path.
2. Add backend authentication path and fallback behavior.
3. Implement command authorization by role map.
4. Add accounting records for success/failure events.
5. Run tests: `pytest -m "lab32 and exercise"`.

## Advanced extensions

- Add backend timeout vs hard-fail policy controls.
- Add per-command accounting payload metadata.
- Add method lists (auth order chains) per line/transport type.

## Simplifications

- No encrypted credential transport modeling.
- No full TACACS+/RADIUS packet parsing.

## Tests

```bash
pytest -m "lab32 and exercise"
```

## Exit criteria

- Auth fallback behavior is deterministic.
- Authorization respects role policy.
- Accounting captures key events.
