# Roadmap

This roadmap extends the implemented lab track (`lab01`-`lab16`) with additional advanced topics.

## Planned labs

1. `lab17_isis`
   - IS-IS L1/L2 flooding and SPF behavior.
2. `lab18_ospf_multi_area`
   - ABR behavior, summary LSAs, inter-area preference.
3. `lab19_bgp_rr`
   - Route reflection, cluster-list loop avoidance.
4. `lab20_bgp_multihoming`
   - inbound/outbound traffic engineering with policy.
5. `lab21_lacp`
   - member state, bundle selection, hashing choices.
6. `lab22_qos_marking`
   - DSCP marking and queue policy simulation.
7. `lab23_segment_routing_basics`
   - SR-MPLS label stack behavior and TI-LFA concepts.
8. `lab24_chaos_resilience`
   - randomized fault injection and convergence SLO checks.

## Scaling rules

- Add one new capability flag per lab family in `labs/capabilities.json`.
- Add one contract test for each new subsystem API surface.
- Keep exercise tests deterministic and scenario-driven where possible.
