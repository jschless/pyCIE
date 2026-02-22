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
