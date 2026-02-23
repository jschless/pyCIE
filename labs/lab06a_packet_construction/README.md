# Lab 06a: Packet Construction

## Goal

Build deterministic packet header stacks (Ethernet, VLAN, IPv4, TCP/UDP) and validate header ordering/payload consistency.

## Standards references

- Ethernet encapsulation: RFC 894 — https://datatracker.ietf.org/doc/html/rfc894
- IPv4 base: RFC 791 — https://datatracker.ietf.org/doc/html/rfc791
- VLAN tagging background: IEEE 802.1Q — https://standards.ieee.org/ieee/802.1Q/7283/

## Files to implement

- `src/pycie/protocols/packet_construction.py`
  - `PacketConstructionProcess.build_packet`
  - `PacketConstructionProcess.build_ipv4_udp`
  - `PacketConstructionProcess.build_ipv4_tcp`
  - `PacketConstructionProcess.insert_vlan_tag`
  - `PacketConstructionProcess.normalize_transport_lengths`
  - `PacketConstructionProcess.validate_packet`
- `src/pycie/model/packet.py`
  - `PacketStack.validate_stack_order`
  - `PacketStack.compute_payload_length`

## Implementation hints

- Validate stack order outer -> inner.
- Reject VLAN tags that are not directly below Ethernet.
- Reject TCP/UDP headers without an IPv4/IPv6 header above them.
- Keep errors deterministic with explicit reason strings.

## Step-by-step implementation

1. Run tests once:

```bash
pytest -m "lab06a and exercise"
```

2. Implement packet stack validation rules.
3. Implement packet builders for UDP and TCP paths.
4. Implement VLAN insertion and length normalization helpers.
5. Re-run tests:

```bash
pytest -m "lab06a and exercise"
```

## Fast feedback commands

```bash
pytest tests/labs/test_lab06a_packet_construction.py -q
pytest tests/labs/test_lab06a_packet_construction_edge_cases.py -q
```

## Common mistakes

- Treating inner-to-outer order as valid packet order.
- Allowing VLAN tags without Ethernet outer header.
- Forgetting to derive UDP length from payload size.

## Simplifications

- No binary serialization/deserialization.
- No checksum offload model.
- No MTU/fragmentation behavior.

## Tests

```bash
pytest -m "lab06a and exercise"
```

## Exit criteria

- Packet stack validation returns deterministic pass/fail reasons.
- TCP/UDP packet builders produce expected header chains.
- VLAN insertion behavior is deterministic and validated.
