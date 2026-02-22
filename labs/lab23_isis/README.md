# Lab 23: IS-IS L1/L2 Foundations

## Goal

Implement a simplified IS-IS process with LSP installation, sequence handling, and per-level SPF.

## Standards references

- IS-IS for IP: RFC 1195 — https://datatracker.ietf.org/doc/html/rfc1195
- IS-IS extensions for traffic engineering context: RFC 5305 — https://datatracker.ietf.org/doc/html/rfc5305
- IS-IS protocol extensions index: RFC 5308 — https://datatracker.ietf.org/doc/html/rfc5308

## Files to implement

- `src/pycie/protocols/isis.py`
  - `ISISProcess.on_start`
  - `ISISProcess.on_frame`
  - `ISISProcess.originate_lsp`
  - `ISISProcess.install_lsp`
  - `ISISProcess.run_spf`
  - `ISISProcess.compute_routing_table`

## Step-by-step implementation

1. Implement LSP sequence handling (`install_lsp`) first.
2. Implement local origination (`originate_lsp`) with deterministic link ordering.
3. Implement SPF with deterministic tie-break behavior.
4. Add level preference logic in `compute_routing_table` (prefer L1 over L2 where both exist).
5. Wire `on_start` and `on_frame`.
6. Run tests: `pytest -m "lab23 and exercise"`.

## Advanced extensions

- Add overload-bit behavior for transit suppression with explicit exceptions.
- Add LSP aging, refresh, and purge behavior.
- Add pseudonode/LAN adjacency modeling.

## Simplifications

- No DIS election or IIH adjacency FSM.
- No true TLV parser/serializer.
- No multi-topology support.

## Tests

```bash
pytest -m "lab23 and exercise"
```

## Exit criteria

- Newer LSPs replace old state deterministically.
- SPF output is deterministic for ties.
- L1/L2 route preference is correct.
