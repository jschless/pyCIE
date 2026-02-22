# Lab 33: DHCP Services

## Goal

Implement DHCPv4 discover/request/ack behavior with lease aging and relay helper behavior.

## Standards references

- DHCPv4: RFC 2131 — https://datatracker.ietf.org/doc/html/rfc2131
- DHCP options: RFC 2132 — https://datatracker.ietf.org/doc/html/rfc2132
- Relay agent information option: RFC 3046 — https://datatracker.ietf.org/doc/html/rfc3046

## Files to implement

- `src/pycie/protocols/dhcp.py`
  - `DHCPServer.handle_discover`
  - `DHCPServer.handle_request`
  - `DHCPServer.renew`
  - `DHCPServer.release`
  - `DHCPServer.age_leases`
  - `DHCPServer.relay`

## Step-by-step implementation

1. Implement deterministic offer allocation from a pool.
2. Implement request validation and ACK/NAK behavior.
3. Implement lease renew/release/aging logic.
4. Implement relay helper behavior (`giaddr`).
5. Run tests: `pytest -m "lab33 and exercise"`.

## Advanced extensions

- Add INIT-REBOOT and SELECTING states explicitly.
- Add per-interface pools and option handling.
- Add DHCPv6 parity in a follow-up lab.

## Simplifications

- No broadcast/unicast transmission timing model.
- No option 82 policy decisions beyond relay stamp.

## Tests

```bash
pytest -m "lab33 and exercise"
```

## Exit criteria

- Lease allocation and reuse are deterministic.
- Expired leases return to pool.
- Invalid/out-of-pool requests are NAKed.
