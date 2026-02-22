# Lab 10: RSTP Proposal/Agreement

## Goal

Implement a simplified rapid spanning tree flow including proposal/agreement behavior.

## Standards references

- IEEE 802.1w: https://standards.ieee.org/ieee/802.1w/11858/
- IEEE 802.1D revisions: https://standards.ieee.org/ieee/802.1D/7020/

## Files to implement

- `src/pycie/protocols/rstp.py`
  - `RSTPProcess.on_start`
  - `RSTPProcess.on_frame`
  - `RSTPProcess.process_bpdu`
  - `RSTPProcess.transmit_bpdu`

## Simplifications

- Topology change notifications omitted.
- Full timer profile tuning omitted.

## Tests

```bash
pytest -m "lab10 and exercise"
```

## Exit criteria

- Root path and port roles converge deterministically.
- Proposal/agreement transitions are internally consistent.
