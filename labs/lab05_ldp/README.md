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

## Implementation hints

- Local label bindings are stored in `self.lib` and should be stable per prefix.
- Remote bindings are nested by peer: `self.remote_bindings[peer_id][prefix]`.
- Labels should come from `self.label_counter` and remain deterministic across runs.
- `advertise_bindings` should reflect the current local LIB view.
- `build_lfib` should produce a deterministic per-prefix tuple, even with multiple peers.

## Step-by-step implementation plan

1. Run the full lab:

```bash
pytest -m "lab05 and exercise"
```

2. Implement `allocate_local_label`.
   - Return existing label if already allocated.
   - Otherwise allocate next label and increment counter.

3. Implement `process_label_mapping`.
   - Record inbound peer label by prefix.
   - Preserve per-peer isolation.

4. Implement `advertise_bindings`.
   - Emit current local mappings as `LabelMapping` objects.
   - Keep output deterministic (stable ordering).

5. Implement `build_lfib`.
   - Merge local and remote binding views into a prefix projection.
   - Preserve a stable peer-choice rule when multiple remote bindings exist.

6. Wire dispatch methods (`on_frame`, optional startup behavior in `on_start`).
   - Parse `LDPHello` and `LabelMapping` payloads correctly.

7. Re-run tests:

```bash
pytest -m "lab05 and exercise"
```

## Fast feedback commands

```bash
pytest tests/labs/test_lab05_ldp.py -k allocate_local_label -q
pytest tests/labs/test_lab05_ldp.py -k process_label_mapping -q
pytest tests/labs/test_lab05_ldp.py -k advertise_bindings -q
pytest tests/labs/test_lab05_ldp.py -k build_lfib -q
```

## Common mistakes

- Reallocating a new label for an existing prefix.
- Flattening remote bindings instead of tracking by peer.
- Returning nondeterministic advertisement/LFIB ordering.
- Mixing local and remote labels in the wrong tuple position.

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
