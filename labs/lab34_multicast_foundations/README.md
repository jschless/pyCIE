# Lab 34: Multicast Foundations

## Goal

Implement group membership state and simplified RPF-checked forwarding for (S,G) flows.

## Standards references

- IGMPv2: RFC 2236 — https://datatracker.ietf.org/doc/html/rfc2236
- IGMPv3: RFC 3376 — https://datatracker.ietf.org/doc/html/rfc3376
- PIM-SM: RFC 7761 — https://datatracker.ietf.org/doc/html/rfc7761

## Files to implement

- `src/pycie/protocols/multicast.py`
  - `MulticastProcess.join_group`
  - `MulticastProcess.leave_group`
  - `MulticastProcess.install_rpf_route`
  - `MulticastProcess.expected_rpf_interface`
  - `MulticastProcess.compute_egress_interfaces`
  - `MulticastProcess.process_data`

## Step-by-step implementation

1. Implement membership add/remove behavior.
2. Implement RPF route lookup with longest-prefix match.
3. Implement forwarding egress selection (exclude ingress).
4. Persist (S,G) state from data processing.
5. Run tests: `pytest -m "lab34 and exercise"`.

## Advanced extensions

- Add (*,G) shared tree state and RP behavior.
- Add prune timers and state expiration.
- Add source-specific multicast policy filters.

## Simplifications

- No full PIM hello/join/prune packet model.
- No DR election.

## Tests

```bash
pytest -m "lab34 and exercise"
```

## Exit criteria

- RPF failures suppress forwarding.
- Membership drives outgoing interface state.
- (S,G) entries update deterministically.
