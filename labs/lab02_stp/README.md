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

## Implementation hints

- Local ports are in `self.ports` (`dict[str, STPPort]`).
- Local bridge identity is `self.bridge_id`.
- Current root view is tracked by:
  - `self.root_id`
  - `self.root_cost`
  - `self.root_port`
- Incoming BPDU for parsing logic is usually in `frame.payload` from `on_frame`.
- Python tuple comparison is useful for deterministic BPDU ordering, for example:
  - `(root_id, path_cost, bridge_id, port_id)`

## Step-by-step implementation plan

1. Run the lab once to see baseline failures:

```bash
pytest -m "lab02 and exercise"
```

2. Implement `should_forward_data`.
   - Return `True` only when the selected port state is forwarding.

3. Implement `recompute_port_states`.
   - If local bridge is root, all ports should be designated/forwarding.
   - If not root:
     - root port should be role `ROOT`, state `FORWARDING`.
     - non-root ports should be non-forwarding (`BLOCKING` or equivalent for your model).

4. Implement `build_bpdu`.
   - Build a `BPDU` with current local root view (`self.root_id`, `self.root_cost`, `self.bridge_id`) and local port ID.

5. Implement `process_bpdu`.
   - Parse candidate root information from inbound BPDU.
   - Compare candidate tuple against current local tuple.
   - If inbound is superior, update:
     - `self.root_id`
     - `self.root_cost`
     - `self.root_port`
   - Recompute port states after a superior update.

6. Implement `on_frame`.
   - Only process frames whose payload is `BPDU`.
   - Call `process_bpdu(...)`.

7. Implement `on_start`.
   - Initialize local root view.
   - Recompute port states.
   - (Optional for this simplified lab) prebuild or trigger initial BPDU behavior.

8. Re-run full lab tests:

```bash
pytest -m "lab02 and exercise"
```

## Fast feedback commands

```bash
pytest tests/labs/test_lab02_stp.py -k forward -q
pytest tests/labs/test_lab02_stp.py -k recompute -q
pytest tests/labs/test_lab02_stp.py -k bpdu -q
```

## Common mistakes

- Failing to recompute states after root changes.
- Not including path cost when comparing inbound root candidates.
- Letting root port remain set when local bridge should be root.
- Returning forwarding for blocked/alternate ports in `should_forward_data`.

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
