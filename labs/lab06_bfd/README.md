# Lab 06: Simplified BFD

## Goal

Implement BFD session bring-up, control packet handling, and timeout detection.

## Standards references

- RFC 5880 (base): https://datatracker.ietf.org/doc/html/rfc5880
- RFC 5881 (single hop): https://datatracker.ietf.org/doc/html/rfc5881

## Files to implement

- `src/pycie/protocols/bfd.py`
  - `BFDProcess.on_start`
  - `BFDProcess.on_frame`
  - `BFDProcess.open_session`
  - `BFDProcess.receive_control`
  - `BFDProcess.transmit_control`
  - `BFDProcess.detect_time_ms`
  - `BFDProcess.check_timeouts`

## Implementation hints

- Session state is tracked in `self.sessions` keyed by peer ID.
- `open_session` should be idempotent for an existing peer.
- Detection time in this lab is a direct multiplication:
  - `required_min_rx_ms * detect_mult`
- `receive_control` should validate discriminator matching before state updates.
- `check_timeouts` should compare elapsed time against detect time and mark expired sessions down.

## Step-by-step implementation plan

1. Run baseline tests:

```bash
pytest -m "lab06 and exercise"
```

2. Implement `open_session`.
   - Allocate unique local discriminators.
   - Return existing session when already present.

3. Implement `detect_time_ms`.
   - Use session multiplier and required RX interval.

4. Implement `receive_control`.
   - Validate `your_discriminator`.
   - Update remote discriminator and timing fields.
   - Apply simplified state transition behavior.

5. Implement `transmit_control` and `on_frame`.
   - Build outbound control from current session state.
   - Dispatch inbound control payloads from `on_frame`.

6. Implement `check_timeouts`.
   - Identify expired sessions.
   - Move expired sessions to down state and return peer IDs.

7. Re-run tests:

```bash
pytest -m "lab06 and exercise"
```

## Fast feedback commands

```bash
pytest tests/labs/test_lab06_bfd.py -k open_session -q
pytest tests/labs/test_lab06_bfd.py -k detect_time_ms -q
pytest tests/labs/test_lab06_bfd.py -k receive_control -q
pytest tests/labs/test_lab06_bfd.py -k check_timeouts -q
```

## Common mistakes

- Assigning duplicate discriminators across peers.
- Updating session state even when discriminator validation should fail.
- Forgetting to update `last_rx_ms` on valid control reception.
- Using `>` instead of `>=` in timeout checks.

## Simplifications

- Asynchronous mode only.
- Single hop.
- Authentication omitted.

## Tests

```bash
pytest -m "lab06 and exercise"
```

## Exit criteria

- Session transitions to `UP` after valid control exchange.
- Detection timer computation is correct.
- Missed control packets force down state at timeout.
