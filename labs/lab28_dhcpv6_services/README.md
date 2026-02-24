# Lab 28: DHCPv6 Services

## Goal

Implement deterministic DHCPv6 lease allocation, renewal/release behavior, and basic relay metadata handling.

## Standards references

- DHCP for IPv6: RFC 8415 — https://datatracker.ietf.org/doc/html/rfc8415
- IPv6 addressing architecture: RFC 4291 — https://datatracker.ietf.org/doc/html/rfc4291

## Files to implement

- `src/pycie/protocols/dhcpv6.py`
  - `DHCPv6Server.handle_solicit`
  - `DHCPv6Server.handle_request`
  - `DHCPv6Server.renew`
  - `DHCPv6Server.release`
  - `DHCPv6Server.age_leases`
  - `DHCPv6Server.relay`

## Step-by-step implementation

1. Implement solicit/advertise behavior with deterministic pool selection.
2. Implement request/reply acceptance and noaddravail responses.
3. Implement lease renewal and release behavior.
4. Implement lease aging.
5. Implement relay helper metadata stamping.
6. Run tests: `pytest -m "lab28 and exercise"`.

## Simplifications

- Single server pool and IA_NA-style behavior only.
- No DHCPv6 option parser.
- No relay encapsulation chain.

## Tests

```bash
pytest -m "lab28 and exercise"
```

## Exit criteria

- Lease allocation and conflicts are deterministic.
- Expired/released leases are reclaimed correctly.
- Relay metadata is preserved correctly across messages.

