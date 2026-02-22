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
