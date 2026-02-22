# Lab 07: IPv4 Forwarding Pipeline

## Goal

Implement longest-prefix matching, tie-breakers, TTL handling, and drop reason classification.

## Standards references

- RFC 791 (IPv4): https://datatracker.ietf.org/doc/html/rfc791
- RFC 1812 (router behavior): https://datatracker.ietf.org/doc/html/rfc1812

## Files to implement

- `src/pycie/forwarding/l3.py`
  - `IPv4Forwarder.install_route`
  - `IPv4Forwarder.remove_route`
  - `IPv4Forwarder.lookup`
  - `IPv4Forwarder.forward`

## Simplifications

- IPv4 unicast only.
- No ECMP in this phase.

## Tests

```bash
pytest -m "lab07 and exercise"
```

## Exit criteria

- Deterministic best-route selection for overlapping prefixes.
- TTL expiration drops packet before forwarding.
