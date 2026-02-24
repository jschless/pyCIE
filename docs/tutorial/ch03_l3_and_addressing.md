# Chapter 3: L3 Forwarding and Addressing

## Why this chapter matters

Most operational incidents come down to route choice, prefix interpretation, and next-hop adjacency state.

## Labs

- `lab06c_ip_subnet_mac_forwarding_basics`
- `lab07_ipv4_forwarding`
- `lab08_arp`
- `lab20_ipv6_nd_forwarding`

## Concepts to master

- CIDR/prefix math and longest-prefix matching
- Admin distance + metric tie-break behavior
- ARP/ND dependency before forwarding
- TTL/hop-limit drop paths

## Hands-on sequence

```bash
pycie run lab06c --student-src dist/student/src
pycie run lab07 --student-src dist/student/src
pycie run lab08 --student-src dist/student/src
pycie run lab20 --student-src dist/student/src
```

Inspect forwarding reasoning:

```bash
pycie run lab07 --student-src dist/student/src --trace-out traces/lab07.jsonl
pycie viz replay --trace traces/lab07.jsonl --event ROUTE_SELECT --event FIB_FORWARD --event FIB_DROP
```

## Checkpoint

You should be able to explain, for any destination IP, the selected prefix, next-hop, and whether forwarding fails because of route or adjacency resolution.

## Chapter navigation

<div class="chapter-nav">
  <a href="../">Course Map</a>
  <a href="../ch02_switching_and_stp/">Previous: Chapter 2</a>
  <a href="../ch04_transport_nat_acl_qos/">Next: Chapter 4</a>
</div>
