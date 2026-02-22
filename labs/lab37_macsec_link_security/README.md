# Lab 37: MACsec Link Security

## Goal

Implement per-interface MACsec policy enforcement and replay protection logic.

## Standards references

- MAC Security (IEEE 802.1AE): https://standards.ieee.org/ieee/802.1AE/7118/

## Files to implement

- `src/pycie/protocols/macsec.py`
  - `MACsecProcess.configure_interface`
  - `MACsecProcess.install_secure_association`
  - `MACsecProcess.validate_ingress`
  - `MACsecProcess.protect_egress`

## Step-by-step implementation

1. Implement per-interface policy/SA state.
2. Enforce cleartext policy behavior.
3. Enforce SAK validation.
4. Implement replay-window logic and cache pruning.
5. Implement egress protection decision behavior.
6. Run tests: `pytest -m "lab37 and exercise"`.

## Advanced extensions

- Add MKA-style key rollover state machine.
- Add secure channel identifier (SCI) matching behavior.
- Add per-priority bypass/control traffic policies.

## Simplifications

- No cryptographic transform implementation.
- No MKA negotiation protocol in this lab.

## Tests

```bash
pytest -m "lab37 and exercise"
```

## Exit criteria

- Replay and stale packet checks are correct.
- Policy mismatch behavior is explicit.
- Egress protection enforces interface policy.
