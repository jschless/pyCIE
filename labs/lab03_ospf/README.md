# Lab 03: Simplified OSPF

## Goal

Implement hello processing, neighbor state updates, LSDB install logic, and SPF computation.

## Standards references

- RFC 2328 (OSPFv2): https://datatracker.ietf.org/doc/html/rfc2328

Suggested reading sections:

- Section 7: Next-hop calculation
- Section 8: SPF calculations
- Section 10: Neighbor data structures
- Section 13: Flooding and LSDB sync

## Files to implement

- `src/pycie/protocols/ospf.py`
  - `OSPFProcess.on_start`
  - `OSPFProcess.on_frame`
  - `OSPFProcess.send_hello`
  - `OSPFProcess.process_hello`
  - `OSPFProcess.originate_router_lsa`
  - `OSPFProcess.install_lsa`
  - `OSPFProcess.run_spf`
  - `OSPFProcess.compute_routing_table`

## Implementation hints

- Neighbor state is tracked in `self.neighbors` keyed by router ID.
- LSAs are stored in `self.lsdb`; only newer sequence numbers should replace existing entries.
- `run_spf` should return a deterministic map: `node -> (cost, first_hop)`.
  - Use stable ordering when costs tie so results do not depend on dict iteration.
- `compute_routing_table` should be derived from `run_spf`, not recomputed independently.
- `on_frame` should only dispatch supported payload types (`OSPFHello`, `RouterLSA`).

## Step-by-step implementation plan

1. Run the full lab once:

```bash
pytest -m "lab03 and exercise"
```

2. Implement `install_lsa`.
   - Accept first-seen LSAs.
   - Accept newer sequence LSAs.
   - Reject stale/equal sequence LSAs.

3. Implement `process_hello`.
   - Ignore mismatched areas.
   - Create/refresh neighbor entries.
   - Advance neighbor state based on whether your router ID appears in the hello neighbor list.

4. Implement SPF (`run_spf`).
   - Start from local router with cost 0.
   - Prefer lower total path cost.
   - Keep tie-break behavior deterministic.

5. Implement `compute_routing_table`.
   - Convert SPF output to destination -> next-hop entries.
   - Exclude the local router ID from final forwarding table.

6. Wire glue methods (`on_start`, `on_frame`, and hello/origination flow).
   - `on_start` should at least originate/install a local LSA baseline.
   - `on_frame` should dispatch and call the processing methods above.

7. Re-run lab tests:

```bash
pytest -m "lab03 and exercise"
```

## Fast feedback commands

```bash
pytest tests/labs/test_lab03_ospf.py -k install_lsa -q
pytest tests/labs/test_lab03_ospf.py -k process_hello -q
pytest tests/labs/test_lab03_ospf.py -k run_spf -q
pytest tests/labs/test_lab03_ospf.py -k routing_table -q
```

## Common mistakes

- Overwriting LSDB entries when sequence is unchanged.
- Forgetting to reject hellos from different area IDs.
- Returning nondeterministic next hops when path costs tie.
- Including the local router as a destination in the computed routing table.

## Simplifications

- Single area only.
- Router LSA only.
- No DR/BDR election.

## Tests

```bash
pytest -m "lab03 and exercise"
```

## Exit criteria

- Neighbor states advance when hellos are received.
- LSDB accepts newer sequence and rejects stale sequence.
- SPF returns deterministic shortest paths.
