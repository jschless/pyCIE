# Lab 21: NAT44 Pipeline

## Goal

Implement a deterministic NAT44 translation pipeline supporting dynamic SNAT/PAT, static DNAT, session aging, and return-path validation.

## Standards references

- Traditional NAT behavior: RFC 3022 — https://datatracker.ietf.org/doc/html/rfc3022
- NAT behavioral requirements (UDP/TCP context): RFC 4787 — https://datatracker.ietf.org/doc/html/rfc4787
- NAT operational considerations: RFC 7857 — https://datatracker.ietf.org/doc/html/rfc7857

## Files to implement

- `src/pycie/protocols/nat44_pipeline.py`
  - `NAT44Pipeline.install_static_rule`
  - `NAT44Pipeline.translate_outbound`
  - `NAT44Pipeline.translate_inbound`
  - `NAT44Pipeline.age_sessions`
  - `NAT44Pipeline._allocate_port`
  - `NAT44Pipeline._find_session_by_translated`

## Implementation hints

- Dynamic session key should include:
  - inside src IP/port
  - outside dst IP/port
  - L4 protocol
- Outbound behavior:
  - create/reuse dynamic session
  - translate source IP/port
- Inbound behavior:
  - apply static DNAT first
  - then dynamic session lookup
  - enforce return-path symmetry for dynamic sessions
- Aging should remove idle sessions deterministically.

## Step-by-step implementation plan

1. Run the lab once:

```bash
pytest -m "lab21 and exercise"
```

2. Implement outbound dynamic SNAT/PAT.
   - validate packet + L4 tuple metadata
   - allocate translated port
   - reuse session if flow already exists

3. Implement inbound static DNAT.

4. Implement inbound dynamic return translation with symmetry checks.

5. Implement session timeout aging.

6. Re-run:

```bash
pytest -m "lab21 and exercise"
```

## Fast feedback commands

```bash
pytest tests/labs/test_lab21_nat44_pipeline.py -k outbound -q
pytest tests/labs/test_lab21_nat44_pipeline.py -k inbound -q
pytest tests/labs/test_lab21_nat44_pipeline_edge_cases.py -k session -q
```

## Common mistakes

- Not persisting session state across packets in same flow.
- Applying dynamic session lookup before static DNAT rules.
- Ignoring return-path mismatch checks.
- Failing to age out stale sessions.

## Simplifications

- No ALG behavior.
- No fragmentation handling.
- No endpoint-independent mapping modes beyond this deterministic model.

## Tests

```bash
pytest -m "lab21 and exercise"
```

## Exit criteria

- SNAT/DNAT/PAT flows translate deterministically.
- Session reuse and timeout behavior are correct.
- Return-path mismatch is rejected predictably.
