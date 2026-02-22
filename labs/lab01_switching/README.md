# Lab 01: Learning Switch

## Goal

Implement source MAC learning, destination lookup, flooding, and MAC aging behavior.

## Standards references

- IEEE 802.1D (bridge behavior): https://standards.ieee.org/ieee/802.1D/7020/
- Ethernet forwarding background: https://datatracker.ietf.org/doc/html/rfc894

## Files to implement

- `src/pycie/protocols/switching.py`
  - `LearningSwitch.on_frame`
  - `LearningSwitch.learn_source_mac`
  - `LearningSwitch.lookup_egress_interfaces`
  - `LearningSwitch.age_mac_table`
  - `LearningSwitch.should_flood`

## Simplifications

- No VLAN support.
- No port security.
- No MAC move dampening.

## Tests

```bash
pytest -m "lab01 and exercise"
```

## Exit criteria

- Unknown unicast floods correctly.
- Known unicast forwards to exactly one egress interface.
- MAC entries age out by timer.
