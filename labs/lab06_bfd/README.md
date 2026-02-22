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
