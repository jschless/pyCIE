# Lab 24: IPv4 Fragmentation and Reassembly

## Goal

Implement deterministic IPv4 fragmentation and reassembly behavior with buffer aging.

## Standards references

- IPv4 fragmentation model: RFC 791 — https://datatracker.ietf.org/doc/html/rfc791
- Router behavior requirements: RFC 1812 — https://datatracker.ietf.org/doc/html/rfc1812

## Files to implement

- `src/pycie/protocols/ipv4_fragmentation_reassembly.py`
  - `IPv4FragmentationReassemblyProcess.fragment`
  - `IPv4FragmentationReassemblyProcess.reassemble`
  - `IPv4FragmentationReassemblyProcess.ingest_fragment`
  - `IPv4FragmentationReassemblyProcess.age_reassembly_buffers`

## Step-by-step implementation

1. Implement fragmentation logic with MTU chunk sizing and MF/offset handling.
2. Honor DF handling and return explicit reason on fragmentation-needed.
3. Implement deterministic reassembly with gap detection.
4. Implement incremental ingest and timeout aging for fragment buffers.
5. Run tests: `pytest -m "lab24 and exercise"`.

## Simplifications

- No IPv4 options header support.
- No checksum validation.
- Overlap policy is deterministic for the lab model.

## Tests

```bash
pytest -m "lab24 and exercise"
```

## Exit criteria

- Fragment offsets/flags are deterministic and valid.
- Reassembly returns full payload only when complete.
- Incomplete/invalid fragment sets fail with explicit reasons.
