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
