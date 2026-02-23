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

## Implementation hints

- Port behavior is mode-dependent (`access` vs `trunk`).
- FDB keys should include VLAN context: `(vlan, mac)`.
- Ingress classification should decide VLAN or drop (`None`).
- Unknown unicast flooding must stay inside VLAN scope and exclude ingress interface.
- Keep flood/egress order deterministic for stable tests.

## Step-by-step implementation plan

1. Run baseline tests:

```bash
pytest -m "lab09 and exercise"
```

2. Implement `ingress_vlan`.
   - Access ports: map untagged traffic to access VLAN.
   - Trunk ports: accept allowed VLAN tags and native VLAN behavior.
   - Reject disallowed VLAN/tag combinations.

3. Implement learning and aging.
   - `learn` updates FDB + timestamp.
   - `age_fdb` removes expired entries.

4. Implement forwarding decision.
   - `lookup_egress` should return known unicast if learned on a different port.
   - Otherwise flood only to ports participating in the same VLAN.

5. Implement egress tag decision.
   - `egress_should_tag` should reflect access/trunk + native VLAN logic.

6. Re-run tests:

```bash
pytest -m "lab09 and exercise"
```

## Fast feedback commands

```bash
pytest tests/labs/test_lab09_vlan.py -k ingress_vlan -q
pytest tests/labs/test_lab09_vlan.py -k disallowed_vlan -q
pytest tests/labs/test_lab09_vlan.py -k lookup_egress -q
pytest tests/labs/test_lab09_vlan.py -k egress_tag -q
```

## Common mistakes

- Learning MAC addresses without VLAN scoping.
- Flooding across VLAN boundaries.
- Forgetting to exclude ingress interface during flood.
- Tagging native VLAN traffic on trunk egress when the model expects untagged.

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
