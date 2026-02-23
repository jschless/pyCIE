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

## Visualization

Capture trace while running this lab:

```bash
pycie run lab07 --trace-out traces/lab07.jsonl
```

Replay route decisions:

```bash
pycie viz replay --trace traces/lab07.jsonl --event ROUTE_LOOKUP --event ROUTE_SELECT --event FIB_FORWARD --event FIB_DROP
```

Expected event patterns:

- Successful forwarding: `ROUTE_LOOKUP` -> `ROUTE_SELECT` -> `FIB_FORWARD`.
- Drop path: `ROUTE_LOOKUP` -> `ROUTE_SELECT` (reason `no_route`) -> `FIB_DROP`.

Advanced exercises:

- Create overlapping prefixes and explain why selected prefix/AD/metric fields changed.
- Compare TTL-expired versus no-route drop reasons.

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
