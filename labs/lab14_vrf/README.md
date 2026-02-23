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

## Implementation hints

- VRFs are independent containers keyed by name in `self.vrfs`.
- Keep strict isolation as the default behavior.
- Unknown VRF names should be handled explicitly (error or guarded behavior per method contract).
- Route leaking should require both:
  - route exists in source VRF
  - source export RT matches destination import RT

## Step-by-step implementation plan

1. Run the tests:

```bash
pytest -m "lab14 and exercise"
```

2. Implement `bind_interface`.
   - Validate VRF exists.
   - Add interface membership to the target VRF.

3. Implement `install_route`.
   - Validate VRF exists.
   - Insert/update prefix next-hop inside that VRF only.

4. Implement `leak_route`.
   - Validate source and destination VRFs.
   - Verify source route exists.
   - Enforce RT policy before copying route into destination VRF.

5. Re-run tests:

```bash
pytest -m "lab14 and exercise"
```

## Fast feedback commands

```bash
pytest tests/labs/test_lab14_vrf.py -k bind_interface -q
pytest tests/labs/test_lab14_vrf.py -k route_leak -q
```

## Common mistakes

- Installing routes into a global table instead of per-VRF route tables.
- Allowing leaks without RT compatibility checks.
- Silently creating unknown VRFs via typo instead of validating names.
- Overwriting destination routes when source prefix is absent.

## Simplifications

- MP-BGP signaling is abstracted in this lab.

## Tests

```bash
pytest -m "lab14 and exercise"
```

## Exit criteria

- Routes remain isolated by default.
- Leak is allowed only when route targets match policy.
