# Lab 22: ICMP Control-Plane Basics

## Goal

Implement deterministic ICMP/ICMPv6 control-plane helpers for ping and traceroute-style diagnostics.

## Standards references

- IPv4: RFC 791 — https://datatracker.ietf.org/doc/html/rfc791
- ICMPv4: RFC 792 — https://datatracker.ietf.org/doc/html/rfc792
- ICMPv6: RFC 4443 — https://datatracker.ietf.org/doc/html/rfc4443
- Traceroute behavior context: RFC 1812 — https://datatracker.ietf.org/doc/html/rfc1812

## Files to implement

- `src/pycie/protocols/icmp_control_plane_basics.py`
  - `ICMPControlPlaneProcess.build_echo_request`
  - `ICMPControlPlaneProcess.build_echo_reply`
  - `ICMPControlPlaneProcess.build_time_exceeded`
  - `ICMPControlPlaneProcess.build_destination_unreachable`
  - `ICMPControlPlaneProcess.traceroute_probe`
  - `ICMPControlPlaneProcess.traceroute_hop_result`

## Step-by-step implementation

1. Implement echo request/reply behavior for IPv4 and IPv6.
2. Implement time-exceeded and destination-unreachable builders.
3. Implement traceroute probe builder with deterministic port/TTL logic.
4. Implement deterministic hop outcome behavior.
5. Run tests: `pytest -m "lab22 and exercise"`.

## Simplifications

- No checksum calculations.
- No wire-format serialization/parsing.
- No ICMP quote payload truncation rules.

## Tests

```bash
pytest -m "lab22 and exercise"
```

## Exit criteria

- Echo and error messages map to correct protocol/version behavior.
- Traceroute outcomes are deterministic for transit vs destination hops.
- Input validation catches invalid probe/packet states.
