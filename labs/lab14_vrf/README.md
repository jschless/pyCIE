# Lab 14: VRF and Route Leaking

## Goal

Implement VRF route separation, interface binding, and RT-governed route leaking.

## Standards references

- RFC 4364 (BGP/MPLS IP VPNs): https://datatracker.ietf.org/doc/html/rfc4364

## Files to implement

- `src/pycie/protocols/vrf.py`
  - `VRFProcess.bind_interface`
  - `VRFProcess.install_route`
  - `VRFProcess.leak_route`

## Simplifications

- MP-BGP signaling is abstracted in this lab.

## Tests

```bash
pytest -m "lab14 and exercise"
```

## Exit criteria

- Routes remain isolated by default.
- Leak is allowed only when route targets match policy.
