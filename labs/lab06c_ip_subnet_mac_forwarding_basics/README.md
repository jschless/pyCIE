# Lab 06c: IP Subnet and MAC Forwarding Basics

## Goal

Practice subnet math, longest-prefix matching, and L2 adjacency requirements for forwarding decisions.

## Standards references

- IPv4 base: RFC 791 — https://datatracker.ietf.org/doc/html/rfc791
- Router behavior: RFC 1812 — https://datatracker.ietf.org/doc/html/rfc1812
- ARP context: RFC 826 — https://datatracker.ietf.org/doc/html/rfc826

## Files to implement

- `src/pycie/protocols/ip_mac_basics.py`
  - `IPMacBasicsProcess.add_interface`
  - `IPMacBasicsProcess.add_static_route`
  - `IPMacBasicsProcess.learn_arp`
  - `IPMacBasicsProcess.explain_lookup`
  - `IPMacBasicsProcess.forward_decision`
  - `IPMacBasicsProcess.prefix_details`

## Implementation hints

- Prefer longest prefix first.
- Prefer connected routes over static routes on equal prefix length.
- Require MAC resolution for next-hop before successful forwarding.
- Keep explanation output explicit (`selected_prefix`, `prefix_length`, `next_hop_ip`).

## Step-by-step implementation

1. Run tests once:

```bash
pytest -m "lab06c and exercise"
```

2. Implement interface/static route stores.
3. Implement lookup explain output.
4. Implement forwarding decision and ARP dependency.
5. Implement subnet detail helper.
6. Re-run tests:

```bash
pytest -m "lab06c and exercise"
```

## Fast feedback commands

```bash
pytest tests/labs/test_lab06c_ip_subnet_mac_forwarding_basics.py -q
pytest tests/labs/test_lab06c_ip_subnet_mac_forwarding_basics_edge_cases.py -q
```

## Common mistakes

- Comparing prefixes as strings instead of parsed networks.
- Returning next-hop MAC for connected routes before ARP learning.
- Failing deterministic tie-break behavior for equal prefixes.

## Simplifications

- IPv4 only in this phase.
- No ECMP groups.
- No recursive next-hop chains beyond one hop.

## Tests

```bash
pytest -m "lab06c and exercise"
```

## Exit criteria

- Prefix match and tie-break behavior are deterministic.
- Forwarding result clearly indicates unresolved MAC versus no route.
- Subnet detail output is accurate and explainable.
