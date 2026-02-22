# Lab 12: IPsec Tunnel Mode Basics

## Goal

Implement simplified SPD/SAD behavior and ESP tunnel encapsulation/decapsulation semantics.

## Standards references

- RFC 4301 (IPsec architecture): https://datatracker.ietf.org/doc/html/rfc4301
- RFC 4303 (ESP): https://datatracker.ietf.org/doc/html/rfc4303

## Files to implement

- `src/pycie/protocols/ipsec.py`
  - `IPsecProcess.outbound`
  - `IPsecProcess.inbound`
- `src/pycie/forwarding/encapsulation.py`
  - `EncapsulationPipeline.encapsulate`
  - `EncapsulationPipeline.decapsulate`

## Simplifications

- Cryptographic operations are modeled as control flags.
- Key exchange is out of scope.

## Tests

```bash
pytest -m "lab12 and exercise"
```

## Exit criteria

- Outbound policy chooses protect/bypass/drop correctly.
- Inbound processing validates SPI and returns expected action.
