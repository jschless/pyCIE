# Lab 39: RIB to FIB Pipeline

## Goal

Implement deterministic route-programming flow from RIB candidates to installed FIB entries with explain traces.

## Standards references

- IPv4 router requirements: RFC 1812 — https://datatracker.ietf.org/doc/html/rfc1812
- CIDR aggregation background: RFC 4632 — https://datatracker.ietf.org/doc/html/rfc4632

## Files to implement

- `src/pycie/protocols/rib_fib_pipeline.py`
  - `RIBFIBPipeline.install_route`
  - `RIBFIBPipeline.withdraw_route`
  - `RIBFIBPipeline.best_route_for_prefix`
  - `RIBFIBPipeline.resolve_next_hop`
  - `RIBFIBPipeline.recompute`
  - `RIBFIBPipeline.lookup`
  - `RIBFIBPipeline.explain`

## Step-by-step implementation

1. Implement per-prefix candidate ranking.
2. Implement recursive next-hop resolution.
3. Implement FIB programming and skip reasons.
4. Implement destination lookup by longest prefix match.
5. Implement trace output for debugging/explainability.
6. Run tests: `pytest -m "lab39 and exercise"`.

## Advanced extensions

- Add async update ordering and convergence timing metrics.
- Add multipath (ECMP) programming behavior.
- Add LFIB coupling for MPLS-labeled routes.

## Simplifications

- No hardware programming queue model.
- No incremental diff engine in this lab.

## Tests

```bash
pytest -m "lab39 and exercise"
```

## Exit criteria

- Best-route and recursion behavior are deterministic.
- Unresolved/looping next-hops are safely skipped.
- Explain traces reflect actual programming decisions.
