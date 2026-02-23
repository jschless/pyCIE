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

## Visualization

Capture trace while running this lab:

```bash
pycie run lab12 --trace-out traces/lab12.jsonl
```

Replay crypto/tunnel transitions:

```bash
pycie viz replay --trace traces/lab12.jsonl --event CRYPTO_ENCRYPT --event CRYPTO_DECRYPT --event ENCAP_PUSH --event ENCAP_POP --event FRAME_DROP
```

Expected event patterns:

- Protect outbound: `CRYPTO_ENCRYPT` then `ENCAP_PUSH`.
- Protect inbound: `CRYPTO_DECRYPT` then `ENCAP_POP`.
- Invalid SPI/header paths: `FRAME_DROP` with IPsec drop reason.

Advanced exercises:

- Compare BYPASS and PROTECT flows; verify only protected traffic includes crypto events.
- Validate decrypt-before-pop ordering in inbound trace.

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
