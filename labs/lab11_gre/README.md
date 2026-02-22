# Lab 11: GRE and IP-in-IP Encapsulation

## Goal

Implement tunnel encapsulation and decapsulation using explicit header-stack transformations.

## Standards references

- RFC 2784 (GRE): https://datatracker.ietf.org/doc/html/rfc2784
- RFC 2890 (GRE extensions): https://datatracker.ietf.org/doc/html/rfc2890
- RFC 2003 (IP-in-IP): https://datatracker.ietf.org/doc/html/rfc2003

## Files to implement

- `src/pycie/protocols/gre.py`
  - `GRETunnelProcess.encapsulate`
  - `GRETunnelProcess.decapsulate`
- `src/pycie/forwarding/encapsulation.py`
  - `EncapsulationPipeline.encapsulate`
  - `EncapsulationPipeline.decapsulate`

## Simplifications

- No PMTUD handling in this lab.
- No fragmentation/reassembly.

## Tests

```bash
pytest -m "lab11 and exercise"
```

## Exit criteria

- GRE encapsulation yields expected outer header order.
- Decapsulation rejects invalid/unknown tunnel traffic.
