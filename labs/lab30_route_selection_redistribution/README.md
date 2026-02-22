# Lab 30: Route Selection and Redistribution

## Goal

Model route choice across competing protocol candidates and implement redistribution with loop-prevention tags.

## Standards references

- IPv4 router requirements (selection behavior background): RFC 1812 — https://datatracker.ietf.org/doc/html/rfc1812
- BGP best-path context: RFC 4271 — https://datatracker.ietf.org/doc/html/rfc4271
- OSPF route preference context: RFC 2328 — https://datatracker.ietf.org/doc/html/rfc2328

## Files to implement

- `src/pycie/protocols/route_selection.py`
  - `RouteSelectionEngine.install_route`
  - `RouteSelectionEngine.withdraw_route`
  - `RouteSelectionEngine.best_route`
  - `RouteSelectionEngine.explain`
  - `RouteSelectionEngine.redistribute`

## Step-by-step implementation

1. Implement candidate storage and replacement semantics.
2. Implement LPM-based selection with deterministic tie-breakers (AD, metric, protocol, next-hop).
3. Implement decision tracing (`explain`) with ranked candidates.
4. Implement redistribution and tag-based loop prevention.
5. Run tests: `pytest -m "lab30 and exercise"`.

## Advanced extensions

- Add protocol-specific tie-breakers (for example eBGP/iBGP distinctions).
- Add per-prefix redistribution policies and deny lists.
- Add route-origin provenance chains for explainability.

## Simplifications

- No full protocol-origin policy language in this lab.
- No recursive next-hop resolution in this module.

## Tests

```bash
pytest -m "lab30 and exercise"
```

## Exit criteria

- Best route is deterministic under ties.
- Explain output matches actual decision.
- Redistribution tagging blocks loops.
