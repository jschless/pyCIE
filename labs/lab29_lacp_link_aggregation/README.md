# Lab 29: LACP Link Aggregation

## Goal

Implement deterministic LACP member synchronization and bundle egress selection.

## Standards references

- Link Aggregation (normative): IEEE 802.1AX — https://1.ieee802.org/tsn/802-1ax-rev/
- Ethernet operational context: RFC 894 — https://datatracker.ietf.org/doc/html/rfc894

## Files to implement

- `src/pycie/protocols/lacp.py`
  - `LACPProcess.add_port`
  - `LACPProcess.receive_lacpdu`
  - `LACPProcess.active_members`
  - `LACPProcess.select_egress`
  - `LACPProcess.age_sessions`

## Step-by-step implementation

1. Implement local port registration.
2. Implement partner update processing and synchronization decisions.
3. Implement active member eligibility logic.
4. Implement deterministic egress selection over active members.
5. Implement stale session aging behavior.
6. Run tests: `pytest -m "lab29 and exercise"`.

## Simplifications

- No full actor/partner state machine message encoding.
- No marker protocol.
- No multi-chassis LAG behavior.

## Tests

```bash
pytest -m "lab29 and exercise"
```

## Exit criteria

- Member activation depends on key/state correctness.
- Egress choice is stable for the same hash and member set.
- Timeout or link-down events remove members predictably.

