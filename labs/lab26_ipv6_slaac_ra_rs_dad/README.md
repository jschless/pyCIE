# Lab 26: IPv6 SLAAC, RA/RS, and DAD

## Goal

Implement IPv6 stateless addressing flow: router advertisements, host autoconfiguration, and DAD state transitions.

## Standards references

- IPv6 addressing architecture: RFC 4291 — https://datatracker.ietf.org/doc/html/rfc4291
- Neighbor Discovery for IPv6: RFC 4861 — https://datatracker.ietf.org/doc/html/rfc4861
- SLAAC: RFC 4862 — https://datatracker.ietf.org/doc/html/rfc4862

## Files to implement

- `src/pycie/protocols/ipv6_slaac.py`
  - `IPv6SLAACProcess.configure_router`
  - `IPv6SLAACProcess.trigger_rs`
  - `IPv6SLAACProcess.emit_due_ra`
  - `IPv6SLAACProcess.autoconfigure_from_ra`
  - `IPv6SLAACProcess.complete_dad`

## Step-by-step implementation

1. Implement per-interface RA configuration.
2. Implement RS trigger and delayed RA emission behavior.
3. Implement SLAAC address derivation from prefix + MAC.
4. Implement DAD completion transitions (`tentative` -> `preferred` or `duplicate`).
5. Run tests: `pytest -m "lab26 and exercise"`.

## Simplifications

- Single-prefix autoconfiguration per interface.
- No full ND packet parsing/serialization.
- No temporary privacy addresses.

## Tests

```bash
pytest -m "lab26 and exercise"
```

## Exit criteria

- RS/RA timing behavior is deterministic.
- SLAAC addresses derive correctly for valid prefixes/MACs.
- DAD transition errors are explicit and reproducible.

