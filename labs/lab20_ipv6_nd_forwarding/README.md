# Lab 20: IPv6 ND Forwarding

## Goal

Implement IPv6 forwarding with longest-prefix route lookup and Neighbor Discovery (ND) resolution queues for unresolved next hops.

## Standards references

- IPv6 addressing architecture: RFC 4291 — https://datatracker.ietf.org/doc/html/rfc4291
- IPv6 Neighbor Discovery: RFC 4861 — https://datatracker.ietf.org/doc/html/rfc4861
- IPv6 base spec (hop limit / forwarding context): RFC 8200 — https://datatracker.ietf.org/doc/html/rfc8200

## Files to implement

- `src/pycie/protocols/ipv6_nd_forwarding.py`
  - `IPv6NDForwarder.install_route`
  - `IPv6NDForwarder.lookup_route`
  - `IPv6NDForwarder.learn_neighbor`
  - `IPv6NDForwarder.age_neighbors`
  - `IPv6NDForwarder.queue_pending`
  - `IPv6NDForwarder.resolve_neighbor`
  - `IPv6NDForwarder.forward`
  - `IPv6NDForwarder.should_solicit`

## Implementation hints

- Keep route selection deterministic:
  - longest prefix first
  - then metric
  - then stable interface/next-hop tie-breaks
- Forwarding behavior should mirror IPv4 style:
  - no IPv6 header -> drop
  - hop-limit expiry -> drop
  - no route -> drop
- For unresolved next-hop:
  - queue packet clone
  - return unresolved reason
  - signal that solicitation is needed

## Step-by-step implementation plan

1. Run the lab once:

```bash
pytest -m "lab20 and exercise"
```

2. Implement route and neighbor stores.

3. Implement route lookup and hop-limit decrement path.

4. Implement unresolved-next-hop queue behavior.

5. Implement ND advertisement resolution and queued packet drain.

6. Implement neighbor aging and solicitation checks.

7. Re-run:

```bash
pytest -m "lab20 and exercise"
```

## Fast feedback commands

```bash
pytest tests/labs/test_lab20_ipv6_nd_forwarding.py -k lookup -q
pytest tests/labs/test_lab20_ipv6_nd_forwarding.py -k unresolved -q
pytest tests/labs/test_lab20_ipv6_nd_forwarding_edge_cases.py -k age -q
```

## Common mistakes

- Forgetting to decrement hop-limit on forwarded packets.
- Mutating original packet instead of forwarding clone.
- Dropping unresolved packets instead of queuing.
- Ignoring neighbor TTL aging.

## Simplifications

- No full ICMPv6 packet parser/serializer.
- No SLAAC/RA logic.
- No multicast listener discovery.

## Tests

```bash
pytest -m "lab20 and exercise"
```

## Exit criteria

- Forwarding and drop reasons are deterministic.
- ND unresolved queue and resolution drain work correctly.
- Neighbor aging and solicitation checks are consistent.
