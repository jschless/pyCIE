# Roadmap and Backlog

This file is the working TODO list for scaling `pyCIE` from simplified protocol logic to more realistic control-plane and forwarding behavior.

Scope:

- Keep current lab sequence (`lab01`-`lab16`) intact.
- Add realism in small steps inside a lab.
- Split into a new lab only when state model or protocol surface changes materially.

## Decision rule: extend vs split

Keep in the same lab when all are true:

- The protocol family is unchanged.
- Existing data structures still fit with additive fields.
- Tests can stay in the same marker (`labXX`) without becoming long integration scenarios.

Split into a new lab when any is true:

- A new per-instance model is needed (per-VLAN/per-VRF/per-SA).
- A new handshake/FSM or signaling protocol appears.
- Encapsulation or forwarding pipeline stages change significantly.
- Test setup complexity jumps from unit behavior to scenario orchestration.

## Existing labs: next realism layer

These items deepen each current lab without changing the overall sequence.

### `lab01_switching`

- [ ] Add MAC move handling with optional move counters.
- [ ] Add bounded MAC table behavior (deterministic eviction policy).
- [ ] Add unknown multicast handling separate from broadcast.
- [ ] Add tests: move update correctness, eviction determinism, multicast flood behavior.
- [ ] Keep out of this lab: 802.1X/port-security enforcement.

### `lab02_stp`

- [ ] Add timer-driven behavior (hello cadence, max-age expiry at model level).
- [ ] Add explicit designated-port election outcomes per segment model.
- [ ] Add topology-change-triggered flush hooks (logical, not full wire format).
- [ ] Add tests: timer expiry reconvergence, designated-port tie-breaks, root loss recovery.
- [ ] Keep out of this lab: per-VLAN spanning tree (PVST/MSTP).

### `lab03_ospf`

- [ ] Add additional LSA classes beyond router-LSA in a constrained model.
- [ ] Add deterministic flooding controls (sequence/age conflict handling).
- [ ] Add SPF trigger policy and throttle semantics.
- [ ] Add tests: LSA replacement ordering, flood suppression, SPF recompute triggers.
- [ ] Keep out of this lab: multi-area ABR behavior and DR/BDR election.

### `lab04_bgp`

- [ ] Expand best-path inputs (`local_pref`, AS path length, MED in scoped conditions).
- [ ] Add withdrawal and implicit-withdraw behavior.
- [ ] Add next-hop reachability gating via RIB lookup hook.
- [ ] Add tests: deterministic best-path ties, withdrawal propagation, next-hop invalidation.
- [ ] Keep out of this lab: full BGP transport/FSM.

### `lab05_ldp`

- [ ] Add label withdraw/release flows and stale mapping cleanup.
- [ ] Add configurable retention mode behavior (liberal vs conservative).
- [ ] Add tests: mode-differentiated label storage and release correctness.
- [ ] Keep out of this lab: ordered-vs-independent control interaction depth.

### `lab06_bfd`

- [ ] Add stricter timer negotiation and detect-time behavior.
- [ ] Add admin-down handling and session hold semantics.
- [ ] Add tests: multiplier edge cases, timeout transitions, admin-state precedence.
- [ ] Keep out of this lab: echo mode, multihop, authentication.

### `lab07_ipv4_forwarding`

- [ ] Add ECMP group programming and deterministic hash bucket simulation.
- [ ] Add recursive next-hop resolution behavior.
- [ ] Add TTL/ICMP exception handling path.
- [ ] Add route decision visibility hooks (why-selected metadata for LPM/AD/metric tie-breaks).
- [ ] Add tests: ECMP balance determinism, recursion invalidation, TTL expiry, route-choice explainability.
- [ ] Keep out of this lab: NAT translation stages.

### `lab08_arp`

- [ ] Add gratuitous ARP update and conflict behavior.
- [ ] Add proxy ARP decision hooks.
- [ ] Add retry/backoff timer model for unresolved neighbors.
- [ ] Add tests: pending-queue flush ordering, gratuitous overwrite policy, proxy decisions.
- [ ] Keep out of this lab: IPv6 ND (different protocol family).

### `lab09_vlan`

- [ ] Add native VLAN handling on trunk ingress/egress.
- [ ] Add explicit allowed-VLAN pruning logic.
- [ ] Add tests: tag add/remove rules, trunk pruning, native VLAN mismatch outcomes.
- [ ] Keep out of this lab: QinQ/provider bridging.

### `lab10_rstp`

- [ ] Add stronger proposal/agreement transition guards.
- [ ] Add edge-port behavior and transition shortcuts.
- [ ] Add topology-change propagation flags (simplified signaling).
- [ ] Add tests: agreement gating, edge-port fast transition, TC-driven behavior.
- [ ] Keep out of this lab: MSTP region/instance mapping.

### `lab11_gre`

- [ ] Add GRE key/sequence/checksum option handling.
- [ ] Add keepalive/health signal hooks for tunnel liveliness.
- [ ] Add tests: option parsing, replay/order checks, liveliness-driven forwarding gate.
- [ ] Keep out of this lab: PMTUD and fragmentation/reassembly.

### `lab12_ipsec`

- [ ] Add richer SPD selector matching (proto/ports/subnets).
- [ ] Add anti-replay window logic.
- [ ] Add SA lifetime and rekey trigger model (without IKE yet).
- [ ] Add tests: selector precedence, replay window acceptance, SA rollover behavior.
- [ ] Keep out of this lab: dynamic key exchange protocol.

### `lab13_bgp_policy`

- [ ] Add prefix-list range operators (`ge`/`le`) and ordered match semantics.
- [ ] Add community match/set behavior.
- [ ] Add route-map sequence control with permit/deny continuation rules.
- [ ] Add tests: sequence ordering, community rewrite determinism, exact-vs-range precedence.
- [ ] Keep out of this lab: RPKI/validation feeds.

### `lab14_vrf`

- [ ] Add explicit RT import/export policy matrices.
- [ ] Add leak guardrails (deny by default, explicit permits).
- [ ] Add tests: leak policy enforcement, route visibility isolation, RT precedence.
- [ ] Keep out of this lab: full MP-BGP VPNv4/v6 signaling model.

### `lab15_mpls_forwarding`

- [ ] Add PHP vs explicit-null forwarding behavior.
- [ ] Add TTL propagation modes (`uniform`/`pipe`) in simplified form.
- [ ] Add ICMP exception generation hooks across label stack handling.
- [ ] Add tests: label pop/swap correctness, TTL mode differences, exception paths.
- [ ] Keep out of this lab: RSVP-TE or SR policy programming.

### `lab16_capstone`

- [ ] Add larger failure matrix coverage (link, node, policy, tunnel, label failures).
- [ ] Add convergence timing assertions and bounded-SLO checks.
- [ ] Add compliance assertions for route-policy intent.
- [ ] Add tests: scenario matrix with deterministic seeds and explicit SLO checks.
- [ ] Keep out of this lab: randomized chaos/perf long-run harness.

## Proposed new labs (`lab17+`)

These are prioritized additions after the current sequence.

### Priority 1: core protocol realism gaps

1. `lab17_bgp_fsm_transport`
   - Why separate: introduces full BGP session lifecycle and transport modeling.
   - Prereqs: `lab04`, `lab13`.
   - Deliverables: OPEN/KEEPALIVE/UPDATE/NOTIFICATION state progression, timer handling, reset semantics.
   - Tests: FSM transition table tests, timer-driven disconnect/reconnect, malformed message handling.

2. `lab18_ospf_multi_area`
   - Why separate: introduces ABR-specific inter-area logic and additional LSA classes.
   - Prereqs: `lab03`, `lab07`.
   - Deliverables: area-local LSDB partitions, summary origination, inter-area path preference.
   - Tests: ABR route generation, area isolation, summary preference/tie cases.

3. `lab19_ikev2_for_ipsec`
   - Why separate: key exchange and SA negotiation are distinct from dataplane SPD/SAD logic.
   - Prereqs: `lab12`.
   - Deliverables: IKE SA + child SA lifecycle model, rekey flows, policy-to-SA binding.
   - Tests: negotiation success/failure paths, rekey overlap windows, selector mismatch outcomes.

4. `lab20_ipv6_nd_forwarding`
   - Why separate: new L3 family and neighbor discovery model.
   - Prereqs: `lab07`, `lab08`.
   - Deliverables: IPv6 forwarding basics, ND cache, solicit/advertise resolution queue.
   - Tests: next-hop resolution queueing, neighbor timeout, forwarding parity vs IPv4 cases.

5. `lab21_nat44_pipeline`
   - Why separate: introduces address/port translation stage and session tables.
   - Prereqs: `lab07`, `lab08`, `lab14`.
   - Deliverables: SNAT/DNAT/PAT flow handling, timeout/aging model, return-path symmetry checks.
   - Tests: translation creation/reuse/expiry, collision handling, deterministic mapping rules.

6. `lab22_mstp_or_pvst`
   - Why separate: per-VLAN/per-instance tree state multiplies STP model complexity.
   - Prereqs: `lab02`, `lab09`, `lab10`.
   - Deliverables: instance mapping, per-instance root/role computation, VLAN-to-instance behavior.
   - Tests: per-instance convergence, VLAN isolation, root variance across instances.

### Priority 2: scale and service-provider depth

7. `lab23_isis`
   - Prereqs: `lab03`, `lab07`.
   - Deliverables: L1/L2 flooding and SPF behavior.
   - Tests: level scoping, LSP aging/refresh, deterministic SPF ties.

8. `lab24_bgp_route_reflection`
   - Prereqs: `lab17`, `lab13`.
   - Deliverables: RR cluster behavior, originator-id and cluster-list loop prevention.
   - Tests: reflection correctness, loop avoidance, best-path consistency under RR topology.

9. `lab25_bgp_multihoming`
   - Prereqs: `lab17`, `lab13`, `lab14`.
   - Deliverables: inbound/outbound traffic engineering policy patterns.
   - Tests: policy-driven primary/backup selection, failure failover, route leak guardrails.

10. `lab26_lacp`
   - Prereqs: `lab01`, `lab07`.
   - Deliverables: member negotiation state, bundle activation, hash-based distribution model.
   - Tests: actor/partner mismatch handling, min-links logic, member flap behavior.

11. `lab27_qos_marking_queueing`
   - Prereqs: `lab07`, `lab13`.
   - Deliverables: DSCP classification, marking policy, queue service model.
   - Tests: policy classification determinism, queue starvation protection, drop precedence.

12. `lab28_segment_routing_basics`
   - Prereqs: `lab15`, `lab23`.
   - Deliverables: SR-MPLS segment list programming and forwarding behavior.
   - Tests: label stack construction, path steering correctness, TI-LFA style reroute checks.

13. `lab29_chaos_resilience`
   - Prereqs: `lab16` plus at least two of `lab24`/`lab25`/`lab28`.
   - Deliverables: randomized failure harness with bounded convergence objectives.
   - Tests: deterministic seed replay, SLO pass/fail reporting, failure taxonomy coverage.

### Priority 3: requested enterprise services, security, and overlays

14. `lab30_route_selection_redistribution`
   - Why separate: formalizes multi-source route selection behavior (LPM, AD, metric, protocol tie-breaks) and redistribution controls.
   - Prereqs: `lab03`, `lab04`, `lab07`, `lab14`.
   - Deliverables: explicit route-choice engine with explainable decision traces, protocol-database-to-RIB flow modeling, redistribution policy/tags, loop-avoidance controls.
   - Tests: cross-protocol candidate selection, AD/metric tie cases, redistribution loop-prevention scenarios.

15. `lab31_acl_filtering`
   - Why separate: introduces policy enforcement in the forwarding pipeline with ordered rule semantics.
   - Prereqs: `lab07`, `lab08`, `lab13`.
   - Deliverables: standard/extended IPv4 ACL model, optional IPv6 ACL parity model, direction/application points.
   - Tests: first-match behavior, implicit deny, rule ordering regressions, control-plane vs data-plane attachment checks.

16. `lab32_aaa_access_control`
   - Why separate: adds authentication/authorization/accounting state and external identity integration behavior.
   - Prereqs: `lab13`, `lab16`.
   - Deliverables: local user fallback, TACACS+/RADIUS-style backend abstraction, role/privilege policy mapping.
   - Tests: backend reachable/unreachable fallback, authorization denial paths, accounting record generation.

17. `lab33_dhcp_services`
   - Why separate: introduces client/server/relay state machines and lease lifecycles.
   - Prereqs: `lab07`, `lab08`, `lab14`.
   - Deliverables: DHCPv4 lease allocation and relay behavior, optional DHCPv6 parity extension.
   - Tests: discover-offer-request-ack flow, lease renewal/expiry, relay option handling and failure cases.

18. `lab34_multicast_foundations`
   - Why separate: introduces group membership and tree-building control-plane not present in unicast labs.
   - Prereqs: `lab03`, `lab07`, `lab08`.
   - Deliverables: IGMP membership tracking plus simplified PIM-SM style tree logic.
   - Tests: join/prune behavior, RPF checks, source/group state transitions, failover convergence.

19. `lab35_vxlan_overlay_data_plane`
   - Why separate: adds NVO tunnel encapsulation and tenant-VNI forwarding domain mapping.
   - Prereqs: `lab09`, `lab11`, `lab14`.
   - Deliverables: VXLAN encapsulation/decapsulation, VNI-to-bridge-domain mapping, flood/learn handling in overlay context.
   - Tests: VNI isolation, encapsulation correctness, underlay path loss behavior.

20. `lab36_evpn_control_plane`
   - Why separate: introduces EVPN route types and control-plane MAC/IP advertisement semantics.
   - Prereqs: `lab25`, `lab35`.
   - Deliverables: EVPN RT2/RT5-like simplified exchange model, multihoming behavior in constrained scope.
   - Tests: control-plane learning vs data-plane learning precedence, mobility events, split-horizon behavior.

21. `lab37_macsec_link_security`
   - Why separate: link-layer encryption/integrity introduces per-link secure channel association logic.
   - Prereqs: `lab01`, `lab09`, `lab16`.
   - Deliverables: MACsec policy model, secure/non-secure adjacency behavior, replay-protect sequencing abstraction.
   - Tests: policy mismatch drops, replay-window checks, secure-link fail/open-close behavior.

### Priority 4: router database internals and decision flow

22. `lab38_control_plane_databases`
   - Why separate: isolates protocol databases as first-class objects so students can reason about "where routes live" before best-path selection.
   - Prereqs: `lab03`, `lab04`, `lab05`, `lab13`.
   - Deliverables: explicit OSPF LSDB, BGP Adj-RIB-In/Loc-RIB, LDP label database views with provenance and timestamps.
   - Tests: database insert/replace/withdraw correctness, provenance tracking, deterministic conflict handling.

23. `lab39_rib_to_fib_pipeline`
   - Why separate: makes the route programming pipeline explicit from candidate routes to forwarding decisions.
   - Prereqs: `lab07`, `lab08`, `lab15`, `lab30`, `lab38`.
   - Deliverables: RIB best-route selection (LPM, AD, metric, protocol tie-breaks), recursive next-hop resolution, FIB/LFIB programming trace outputs.
   - Tests: step-by-step route-selection assertions, recursion failure behavior, RIB-change to FIB-update propagation timing.

## Test architecture expectations for all future labs

- Add one exercise suite file: `tests/labs/test_labXX_<topic>.py`.
- Keep setup deterministic; avoid hidden ordering dependence.
- Add explicit edge-case tests before happy-path integration tests.
- Prefer protocol-unit tests first, then scenario tests only when cross-protocol behavior is essential.
- Mark tests with both `exercise` and `labXX`.

## Capability matrix updates

When a roadmap item moves to implementation:

- Add capability flags in `labs/capabilities.json` at feature granularity.
- Record default status (`planned`, `partial`, `complete`) for each capability.
- Tie each new test group to one capability family.
