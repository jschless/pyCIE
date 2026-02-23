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

## Implementation hints

- This lab models control decisions, not cryptography.
- Outbound flow:
  - match SPD policy, then decide `protect`/`bypass`/`drop`.
- Protect action requires a valid SA lookup by SPI in SAD.
- Inbound flow should validate ESP framing and SPI existence before decapsulation.
- Keep action strings/enums consistent with the model (`protect`, `bypass`, `drop`).

## Step-by-step implementation plan

1. Run baseline tests:

```bash
pytest -m "lab12 and exercise"
```

2. Implement outbound SPD/SAD logic.
   - Parse IPv4 headers from packet stack.
   - Apply first matching policy semantics.
   - Build protected packet for `protect` when SA is available.

3. Implement inbound ESP handling.
   - Non-ESP traffic can bypass in this simplified lab.
   - ESP packets with unknown SPI should drop.
   - Valid ESP traffic should decapsulate and return protected action.

4. Implement/verify tunnel-mode behavior in `EncapsulationPipeline` for IPsec mode.

5. Re-run tests:

```bash
pytest -m "lab12 and exercise"
```

## Fast feedback commands

```bash
pytest tests/labs/test_lab12_ipsec.py -k outbound -q
pytest tests/labs/test_lab12_ipsec.py -k inbound -q
```

## Common mistakes

- Protecting traffic without verifying SA existence.
- Dropping all non-ESP inbound traffic when bypass is expected.
- Forgetting to strip both outer IPv4 + ESP headers on successful inbound processing.
- Returning inconsistent action values compared to policy model.

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
