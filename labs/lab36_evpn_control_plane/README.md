# Lab 36: EVPN Control Plane

## Goal

Implement EVPN route import, MAC/IP best-path behavior, and route withdrawal handling.

## Standards references

- BGP MPLS-based EVPN: RFC 7432 — https://datatracker.ietf.org/doc/html/rfc7432
- EVPN overlays: RFC 8365 — https://datatracker.ietf.org/doc/html/rfc8365

## Files to implement

- `src/pycie/protocols/evpn.py`
  - `EVPNControlPlane.import_route`
  - `EVPNControlPlane.withdraw_route`
  - `EVPNControlPlane.recompute`
  - `EVPNControlPlane.resolve_mac`
  - `EVPNControlPlane.resolve_prefix`

## Step-by-step implementation

1. Implement route-target import policy checks.
2. Build Adj-RIB-In storage and replacement semantics.
3. Implement deterministic best-path behavior for RT2 and RT5.
4. Implement route withdrawal and recompute behavior.
5. Run tests: `pytest -m "lab36 and exercise"`.

## Advanced extensions

- Add all-active multihoming aliasing semantics.
- Add ARP/ND synchronization route handling.
- Add split-horizon labels/ESI behavior model.

## Simplifications

- No full MP-BGP session state in this lab.
- Only constrained RT2/RT5 behavior.

## Tests

```bash
pytest -m "lab36 and exercise"
```

## Exit criteria

- Import policy controls visibility.
- Mobility sequence tie-breaks are deterministic.
- Withdraws converge to remaining best paths.
