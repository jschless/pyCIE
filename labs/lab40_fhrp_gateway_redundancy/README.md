# Lab 40: First-Hop Redundancy

## Goal

Implement deterministic first-hop gateway election, failover, and preemption behavior.

## Standards references

- VRRP for IPv4/IPv6: RFC 5798 — https://datatracker.ietf.org/doc/html/rfc5798
- Router requirements context: RFC 1812 — https://datatracker.ietf.org/doc/html/rfc1812

## Files to implement

- `src/pycie/protocols/fhrp.py`
  - `FHRPProcess.register_router`
  - `FHRPProcess.elect_master`
  - `FHRPProcess.update_router`
  - `FHRPProcess.current_virtual_mac`
  - `FHRPProcess.failover_elapsed_ms`

## Step-by-step implementation

1. Implement router registration into the FHRP group.
2. Implement deterministic master election with tie-break behavior.
3. Implement failover and preemption updates.
4. Implement virtual MAC derivation helper.
5. Implement failover timing helper.
6. Run tests: `pytest -m "lab40 and exercise"`.

## Simplifications

- Single group model in one process.
- No advertisement packet transport.
- No load-sharing modes.

## Tests

```bash
pytest -m "lab40 and exercise"
```

## Exit criteria

- Active gateway election is deterministic.
- Failover and preemption behavior is explicit and testable.
- Virtual MAC and failover timing helpers are stable and predictable.

