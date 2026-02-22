# Lab 09: VLAN Access and Trunk Forwarding

## Goal

Implement VLAN classification and VLAN-aware forwarding decisions on access and trunk ports.

## Standards references

- IEEE 802.1Q: https://standards.ieee.org/ieee/802.1Q/7283/

## Files to implement

- `src/pycie/forwarding/l2.py`
  - `BridgeDomain.ingress_vlan`
  - `BridgeDomain.learn`
  - `BridgeDomain.lookup_egress`
  - `BridgeDomain.egress_should_tag`
  - `BridgeDomain.age_fdb`

## Simplifications

- Single spanning-tree instance in this lab.
- QinQ not required.

## Tests

```bash
pytest -m "lab09 and exercise"
```

## Exit criteria

- Access ports map untagged traffic to configured VLAN.
- Trunks accept only allowed VLANs.
- Unknown unicast floods only inside VLAN scope.
