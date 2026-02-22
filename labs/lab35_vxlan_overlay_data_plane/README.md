# Lab 35: VXLAN Overlay Data Plane

## Goal

Implement VNI-scoped learning and forwarding, including overlay encapsulation/decapsulation.

## Standards references

- VXLAN: RFC 7348 — https://datatracker.ietf.org/doc/html/rfc7348

## Files to implement

- `src/pycie/protocols/vxlan.py`
  - `VXLANBridge.add_access_port`
  - `VXLANBridge.add_remote_vtep`
  - `VXLANBridge.learn_local`
  - `VXLANBridge.learn_remote`
  - `VXLANBridge.lookup_egress`
  - `VXLANBridge.encapsulate`
  - `VXLANBridge.decapsulate`

## Step-by-step implementation

1. Implement VNI inventory (access ports and remote VTEPs).
2. Implement VNI-scoped MAC learning.
3. Implement destination lookup (known unicast and flood).
4. Implement VXLAN packet build/extract helpers.
5. Run tests: `pytest -m "lab35 and exercise"`.

## Advanced extensions

- Add head-end replication optimizations by BUM policy.
- Add ARP suppression behavior with EVPN integration.
- Add ECMP underlay path awareness.

## Simplifications

- No underlay routing model in this lab.
- No multicast BUM transport.

## Tests

```bash
pytest -m "lab35 and exercise"
```

## Exit criteria

- VNI isolation is preserved.
- Unknown unicast flood set is deterministic.
- Encapsulation round trip preserves inner frame.
