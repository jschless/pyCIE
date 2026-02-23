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

## Visualization

Capture trace while running this lab:

```bash
pycie run lab11 --trace-out traces/lab11.jsonl
```

Replay tunnel transitions:

```bash
pycie viz replay --trace traces/lab11.jsonl --event ENCAP_PUSH --event ENCAP_POP --event FRAME_DROP
```

Expected event patterns:

- Encapsulation path: `ENCAP_PUSH` with `outer_proto`, `inner_proto`, and `tunnel_type=gre`.
- Valid decapsulation path: `ENCAP_POP`.
- Malformed packet path: `FRAME_DROP` with GRE-specific drop reason.

Advanced exercises:

- Build nested GRE/IPsec stacks and follow one packet with `pycie viz packet`.
- Intentionally corrupt GRE headers and compare drop reasons.

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
