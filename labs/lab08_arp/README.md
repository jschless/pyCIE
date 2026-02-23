# Lab 08: ARP Cache and Resolution Queue

## Goal

Implement ARP cache lifecycle, pending queues for unresolved next hops, and resolution-trigger logic.

## Standards references

- RFC 826 (ARP): https://datatracker.ietf.org/doc/html/rfc826

## Files to implement

- `src/pycie/protocols/arp.py`
  - `ARPProcess.on_frame`
  - `ARPProcess.build_request`
  - `ARPProcess.build_reply`
  - `ARPProcess.process_message`
- `src/pycie/forwarding/arp.py`
  - `ARPTable.lookup`
  - `ARPTable.update`
  - `ARPTable.enqueue_pending`
  - `ARPTable.drain_pending`
  - `ARPTable.needs_request`
  - `ARPTable.age`

## Implementation hints

- This lab spans control-plane (`protocols/arp.py`) and forwarding-cache (`forwarding/arp.py`) behavior.
- ARP table entries should expire by TTL based on `now_ms`.
- Pending packets should preserve order and avoid shared mutable packet references.
- `on_frame` should only process ARP Ethernet frames (`ethertype == 0x0806`) with ARP payload objects.
- `process_message` should always learn sender IP/MAC, then decide whether a reply is needed.

## Step-by-step implementation plan

1. Run baseline tests:

```bash
pytest -m "lab08 and exercise"
```

2. Implement ARP cache methods in `ARPTable`.
   - `update`, `lookup`, and `age`.
   - Validate expiry logic with current time.

3. Implement pending-queue behavior.
   - `enqueue_pending` and `drain_pending`.
   - Keep packet order stable (FIFO behavior per next-hop key).

4. Implement request decision helper.
   - `needs_request` should reflect whether a valid cache entry exists.

5. Implement ARP message builders.
   - `build_request` and `build_reply` should create consistent opcode/field layouts.

6. Implement protocol dispatch and message handling.
   - `on_frame` should parse + dispatch.
   - `process_message` should learn sender and emit replies only for local-target requests.

7. Re-run full tests:

```bash
pytest -m "lab08 and exercise"
```

## Fast feedback commands

```bash
pytest tests/labs/test_lab08_arp.py -k update_and_lookup -q
pytest tests/labs/test_lab08_arp.py -k pending_queue -q
pytest tests/labs/test_lab08_arp.py -k needs_request -q
pytest tests/labs/test_lab08_arp.py -k message_builders -q
```

## Common mistakes

- Not expiring stale ARP entries during lookup/aging.
- Storing original packet objects in pending queue instead of safe copies.
- Replying to non-request messages.
- Replying on requests not targeted to the local interface IP.

## Simplifications

- Gratuitous ARP and proxy ARP omitted.

## Tests

```bash
pytest -m "lab08 and exercise"
```

## Exit criteria

- Cache entries age out correctly.
- Pending packets release after ARP resolution.
- ARP requests are generated only when needed.
