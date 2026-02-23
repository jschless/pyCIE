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

## Implementation hints

- Bridge identity comparison is central:
  - lower `RSTPBridgeId(priority, mac)` wins root election.
- Track root view using `self.root_id` and `self.root_port`.
- Per-port behavior is in `self.ports[if_name]` with role/state/proposed/agreed fields.
- `process_bpdu` should update both root selection and local port transition behavior.
- `transmit_bpdu` should reflect current local root view and requested proposal/agreement flags.

## Step-by-step implementation plan

1. Run the lab tests once:

```bash
pytest -m "lab10 and exercise"
```

2. Implement `on_start`.
   - Initialize root to local bridge.
   - Reset ports into deterministic startup role/state.

3. Implement `process_bpdu`.
   - Ignore unknown ports safely.
   - Apply superior-root updates and root-port selection.
   - Apply proposal/agreement state transitions.

4. Implement `transmit_bpdu`.
   - Build outbound BPDU using local bridge/root context.
   - Preserve proposal/agreement flag inputs in output object.

5. Implement `on_frame`.
   - Dispatch only when payload is an RSTP BPDU.

6. Re-run tests:

```bash
pytest -m "lab10 and exercise"
```

## Fast feedback commands

```bash
pytest tests/labs/test_lab10_rstp.py -k superior_root -q
pytest tests/labs/test_lab10_rstp.py -k transmit_bpdu -q
```

## Common mistakes

- Comparing root candidates with ad-hoc logic instead of bridge ID ordering.
- Updating root ID without updating root port selection.
- Leaving port state unchanged when proposal/agreement flags require transition.
- Building outbound BPDUs with stale root/flag values.

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
