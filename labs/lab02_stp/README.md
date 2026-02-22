# Lab 02: Simplified STP

## Goal

Implement root bridge election, root port selection, and forwarding/blocking decisions.

## Standards references

- IEEE 802.1D (STP): https://standards.ieee.org/ieee/802.1D/7020/
- RSTP lineage reference (optional): https://standards.ieee.org/ieee/802.1w/11858/

## Files to implement

- `src/pycie/protocols/stp.py`
  - `STPProcess.on_start`
  - `STPProcess.on_frame`
  - `STPProcess.build_bpdu`
  - `STPProcess.process_bpdu`
  - `STPProcess.recompute_port_states`
  - `STPProcess.should_forward_data`

## Simplifications

- Classic STP-like ordering; no full RSTP proposal/agreement handshake.
- Static path cost.

## Tests

```bash
pytest -m "lab02 and exercise"
```

## Exit criteria

- Lowest bridge ID becomes root.
- Non-root devices select exactly one root port.
- Looping topology converges to a blocked link path.
