# Lab 04: Simplified BGP

## Goal

Implement session bring-up skeleton, update ingestion, and deterministic best-path selection.

## Standards references

- RFC 4271 (BGP-4): https://datatracker.ietf.org/doc/html/rfc4271
- RFC 4456 (Route Reflection): https://datatracker.ietf.org/doc/html/rfc4456

Suggested reading sections:

- RFC 4271 section 6: Message formats
- RFC 4271 section 9: Route selection

## Files to implement

- `src/pycie/protocols/bgp.py`
  - `BGPProcess.on_start`
  - `BGPProcess.on_frame`
  - `BGPProcess.establish_session`
  - `BGPProcess.process_open`
  - `BGPProcess.process_update`
  - `BGPProcess.best_path`
  - `BGPProcess.recompute_loc_rib`
  - `BGPProcess.export_updates_for_peer`

## Implementation hints

- Peer state is stored in `self.peers`; Adj-RIB-In is `self.adj_rib_in`; best paths live in `self.loc_rib`.
- Treat updates as per-peer candidates:
  - same peer + same prefix should replace prior candidate for that prefix.
- Keep best-path ordering deterministic:
  - local-pref first, then path quality metrics, then stable tie-break keys.
- `recompute_loc_rib` should rebuild from all prefixes present in Adj-RIB-In.
- `export_updates_for_peer` should avoid obvious looped announcements.

## Step-by-step implementation plan

1. Run the lab tests once:

```bash
pytest -m "lab04 and exercise"
```

2. Implement session plumbing (`establish_session`, `process_open`, `on_start`, `on_frame`).
   - Establish only known peers.
   - Validate OPEN against configured peer-AS expectations.

3. Implement `process_update`.
   - Store candidate routes by peer.
   - Trigger best-path recomputation after updates.

4. Implement `best_path`.
   - Gather candidates for one prefix across all peers.
   - Apply deterministic tie-break ordering.

5. Implement `recompute_loc_rib`.
   - Rebuild Loc-RIB from unique prefixes in Adj-RIB-In.
   - Keep exactly one best route per prefix.

6. Implement `export_updates_for_peer`.
   - Return outbound `BGPUpdate` objects for known peers only.
   - Skip updates that would violate your simplified AS-loop check.

7. Re-run tests:

```bash
pytest -m "lab04 and exercise"
```

## Fast feedback commands

```bash
pytest tests/labs/test_lab04_bgp.py -k process_update -q
pytest tests/labs/test_lab04_bgp.py -k best_path -q
pytest tests/labs/test_lab04_bgp.py -k recompute_loc_rib -q
pytest tests/labs/test_lab04_bgp.py -k export_updates -q
```

## Common mistakes

- Appending duplicate candidates for the same peer/prefix instead of replacing.
- Using nondeterministic tie-breakers in best-path logic.
- Forgetting to clear/rebuild Loc-RIB on recompute.
- Exporting routes to unknown peers or sending obvious looped paths.

## Simplifications

- No full TCP model.
- No full attribute set.
- Reduced best-path criteria.

## Tests

```bash
pytest -m "lab04 and exercise"
```

## Exit criteria

- Adj-RIB-In updates are stored by peer.
- Best-path selection is deterministic across ties.
- Loc-RIB reflects best path only.
