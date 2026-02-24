# Chapter 1: Packet Construction

## Why this chapter matters

Before routing, policy, or security, you need to understand how packets are assembled and interpreted layer-by-layer.

## Labs

- `lab06a_packet_construction`
- `lab06b_tcp_udp_fundamentals`

## Concepts to master

- Header ordering: outer to inner encapsulation
- VLAN tag placement rules
- UDP/TCP header fields and flow tuples
- Basic transport validity checks (flag combinations)

## Hands-on sequence

```bash
pycie run lab06a --student-src dist/student/src
pycie run lab06b --student-src dist/student/src
pytest -m "lab06a and exercise"
pytest -m "lab06b and exercise"
```

## Checkpoint

You should be able to explain:

1. Why a TCP or UDP header without an L3 header is invalid.
2. Why deterministic header ordering is required for reproducible tests.
3. How a transport 5-tuple is derived and used later by ACL/NAT/QoS.

## Chapter navigation

<div class="chapter-nav">
  <a href="../">Course Map</a>
  <a href="../ch02_switching_and_stp/">Next: Chapter 2</a>
</div>
