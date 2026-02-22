# Lab 05: Simplified LDP

## Goal

Implement local label allocation, remote binding processing, and LFIB derivation.

## Standards references

- RFC 5036 (LDP): https://datatracker.ietf.org/doc/html/rfc5036
- RFC 3031 (MPLS architecture): https://datatracker.ietf.org/doc/html/rfc3031

## Files to implement

- `src/pycie/protocols/ldp.py`
  - `LDPProcess.on_start`
  - `LDPProcess.on_frame`
  - `LDPProcess.allocate_local_label`
  - `LDPProcess.advertise_bindings`
  - `LDPProcess.process_label_mapping`
  - `LDPProcess.build_lfib`

## Simplifications

- Downstream unsolicited only.
- No liberal/conservative retention mode split.

## Tests

```bash
pytest -m "lab05 and exercise"
```

## Exit criteria

- Labels are stable and unique per prefix.
- Remote label mappings are stored per peer.
- LFIB output is deterministic and internally consistent.
