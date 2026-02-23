# Lab 15: MPLS Forwarding and LFIB

## Goal

Implement LFIB-driven push/swap/pop behavior and FEC-to-label derivation.

## Standards references

- RFC 3031 (MPLS architecture): https://datatracker.ietf.org/doc/html/rfc3031
- RFC 3032 (label stack encoding): https://datatracker.ietf.org/doc/html/rfc3032
- RFC 5036 (LDP): https://datatracker.ietf.org/doc/html/rfc5036

## Files to implement

- `src/pycie/forwarding/mpls.py`
  - `MPLSForwarder.forward`
- `src/pycie/protocols/mpls.py`
  - `MPLSProcess.allocate_label`
  - `MPLSProcess.install_remote_binding`
  - `MPLSProcess.build_lfib_view`

## Implementation hints

- Data plane and control plane are both in scope:
  - forwarding decisions in `MPLSForwarder`
  - label/FEC state in `MPLSProcess`
- LFIB lookup should support unlabeled ingress via a dedicated key path.
- Push/swap/pop operations should preserve packet immutability via cloning.
- Local label allocation must be stable for repeated FEC requests.
- LFIB view generation should stay deterministic when multiple remote peers exist.

## Step-by-step implementation plan

1. Run baseline tests:

```bash
pytest -m "lab15 and exercise"
```

2. Implement `MPLSProcess.allocate_label`.
   - Return existing local label for known FEC.
   - Allocate new labels sequentially for new FECs.

3. Implement `install_remote_binding` and `build_lfib_view`.
   - Store remote bindings by neighbor and FEC.
   - Build projected `(out_label, in_label)` view for each known FEC.

4. Implement `MPLSForwarder.forward`.
   - Resolve top-label/unlabeled entry.
   - Apply push/swap/pop operation semantics.
   - Return consistent drop reasons for missing entries/labels.

5. Re-run tests:

```bash
pytest -m "lab15 and exercise"
```

## Fast feedback commands

```bash
pytest tests/labs/test_lab15_mpls_forwarding.py -k pushes_label -q
pytest tests/labs/test_lab15_mpls_forwarding.py -k builds_lfib -q
```

## Common mistakes

- Reallocating labels for existing FECs.
- Looking up LFIB only by labeled packets and forgetting unlabeled default path.
- Mutating inbound packet header objects directly.
- Building LFIB view with nondeterministic remote-peer choice.

## Simplifications

- Label retention modes are simplified.
- Entropy labels are omitted.

## Tests

```bash
pytest -m "lab15 and exercise"
```

## Exit criteria

- MPLS data-plane operations match LFIB entries.
- Control-plane bindings generate deterministic LFIB view.
