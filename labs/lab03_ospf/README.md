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
