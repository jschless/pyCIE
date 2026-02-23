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

## Implementation hints

- Use Python `ipaddress` helpers for prefix containment and prefix length comparisons.
- Route selection should be deterministic:
  - longest-prefix first, then admin distance, then metric, then stable tie-break keys.
- `forward` should return `(egress_if, packet_out, drop_reason)`.
- Treat TTL expiry as a drop before forwarding.
- Clone packets when modifying headers so callers keep original input intact.

## Step-by-step implementation plan

1. Run the lab tests:

```bash
pytest -m "lab07 and exercise"
```

2. Implement route CRUD (`install_route`, `remove_route`).
   - Avoid accumulating stale duplicate candidates.

3. Implement `lookup`.
   - Filter routes that contain destination IP.
   - Apply LPM and deterministic tie-breaks.

4. Implement `forward`.
   - Validate IPv4 header presence.
   - Enforce TTL decrement/drop behavior.
   - Resolve best route and produce egress decision.

5. Re-run tests:

```bash
pytest -m "lab07 and exercise"
```

## Fast feedback commands

```bash
pytest tests/labs/test_lab07_ipv4_forwarding.py -k longest_prefix -q
pytest tests/labs/test_lab07_ipv4_forwarding.py -k tiebreaks -q
pytest tests/labs/test_lab07_ipv4_forwarding.py -k ttl_expired -q
```

## Common mistakes

- Comparing prefixes as strings instead of parsed networks.
- Forgetting deterministic tie-break behavior when prefix length is equal.
- Modifying input packet in place instead of cloning.
- Returning wrong drop reasons for missing route vs TTL expiry.

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
