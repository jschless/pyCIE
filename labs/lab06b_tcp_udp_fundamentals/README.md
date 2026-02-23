# Lab 06b: TCP/UDP Fundamentals

## Goal

Implement transport-layer fundamentals used by later ACL, NAT, and BGP transport labs: TCP handshake/close behavior, flow tuple extraction, and simplified UDP checksum logic.

## Standards references

- UDP: RFC 768 — https://datatracker.ietf.org/doc/html/rfc768
- TCP: RFC 793 — https://datatracker.ietf.org/doc/html/rfc793
- TCP roadmap context: RFC 9293 — https://datatracker.ietf.org/doc/html/rfc9293

## Files to implement

- `src/pycie/protocols/tcp_udp_fundamentals.py`
  - `validate_tcp_segment`
  - `TCPConnection.send_syn`
  - `TCPConnection.send_fin`
  - `TCPConnection.receive`
  - `TransportFundamentalsProcess.open_session`
  - `TransportFundamentalsProcess.close_session`
  - `TransportFundamentalsProcess.receive_segment`
  - `TransportFundamentalsProcess.extract_flow_tuple`
  - `TransportFundamentalsProcess.compute_udp_checksum`
  - `TransportFundamentalsProcess.build_udp_header`

## Implementation hints

- Keep TCP state transitions explicit and deterministic.
- Validate invalid TCP flag combinations (`SYN+FIN`, `RST+SYN`, `RST+FIN`).
- Return canonical 5-tuples for TCP/UDP packets.
- Keep UDP checksum calculation simple but deterministic.

## Step-by-step implementation

1. Run tests once:

```bash
pytest -m "lab06b and exercise"
```

2. Implement TCP flag validation and state transitions.
3. Implement session wrapper methods.
4. Implement flow tuple extraction from packet headers.
5. Implement UDP checksum helper.
6. Re-run tests:

```bash
pytest -m "lab06b and exercise"
```

## Fast feedback commands

```bash
pytest tests/labs/test_lab06b_tcp_udp_fundamentals.py -q
pytest tests/labs/test_lab06b_tcp_udp_fundamentals_edge_cases.py -q
```

## Common mistakes

- Advancing TCP state on invalid segments.
- Ignoring transport headers when extracting tuples.
- Returning non-deterministic checksum values.

## Simplifications

- No congestion control or retransmission model.
- No SACK/window scaling options.
- No real packet serialization.

## Tests

```bash
pytest -m "lab06b and exercise"
```

## Exit criteria

- Handshake and close transitions are deterministic.
- Invalid flag combinations are rejected.
- Flow tuple and checksum helpers are stable.
