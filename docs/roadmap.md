# Roadmap and Backlog

This file is the working TODO list for scaling `pyCIE` from simplified protocol logic to more realistic control-plane and forwarding behavior.

Scope:

- Keep current lab sequence (`lab01`-`lab16`) intact.
- Add realism in small steps inside a lab.
- Split into a new lab only when state model or protocol surface changes materially.

## Roadmap Ownership Policy (effective February 23, 2026)

- `docs/roadmap.md` is the single source of truth for planning and prioritization.
- `docs/TODO.md` should remain a lightweight pointer, not a second backlog.
- Every sprint item should include:
  - clear deliverables
  - acceptance criteria
  - completion status (`planned`, `in_progress`, `done`)

## Current Product Gaps (highest impact)

These are now the highest-value gaps relative to current protocol breadth:

1. Interactive visualization UX (single-pane "watch it happen" flow).
2. Scenario-driven learning loops (guided failure/reconvergence stories).
3. Realism progression model per lab (`simplified -> realistic` ladder).
4. Contributor scaling and metadata drift prevention.

## 90-Day Execution Plan (February 23, 2026 to May 24, 2026)

This plan is execution-first and acceptance-driven. If capacity is limited, follow the "highest ROI order" section below.

### Sprint 0: Roadmap Hygiene (February 23 to March 1, 2026)

Status: `done`

Deliverables:

- Consolidate roadmap and TODO ownership policy into this file.
- Mark already-completed visualization/CLI capabilities.
- Add status + acceptance criteria pattern for upcoming sprint blocks.

Acceptance criteria:

- `docs/roadmap.md` contains dated sprint plan and priorities.
- `docs/TODO.md` no longer duplicates backlog content.
- Team can answer "what is next" from one file only.

### Sprint 1: Visualization v2 (March 2 to March 22, 2026)

Status: `done`

Deliverables:

- Add `pycie viz web` command to generate a local static HTML viewer from trace JSONL.
- Viewer includes:
  - topology pane
  - packet decode pane (RFC-style field display)
  - timeline scrubber with event selection
- Keep existing CLI visualization paths as backend-compatible data sources.

Acceptance criteria:

- `pycie viz web --trace <file> --out <dir>` generates viewable assets offline.
- Viewer supports node/layer/packet filters and timeline scrubbing.
- At least one contract test validates generation and basic artifact integrity.
- Documentation includes quickstart examples and troubleshooting.

Issue-sized backlog (execution order):

1. `VIZ-01` CLI entrypoint and argument validation
   - Scope: implement `pycie viz web` command plumbing, `--trace`, `--out`, and clear input error messages.
   - Done when: invalid args fail fast, valid args create output directory scaffold.
   - Status: `done`
2. `VIZ-02` Trace normalization adapter
   - Scope: convert existing trace JSONL/events into a stable viewer schema (`topology`, `events`, `packets`).
   - Done when: adapter emits deterministic JSON for identical traces.
   - Depends on: `VIZ-01`
   - Status: `done`
3. `VIZ-03` Static viewer shell
   - Scope: add `index.html`, `styles.css`, `viewer.js`, and local asset loader without external network dependencies.
   - Done when: viewer opens directly from filesystem and loads normalized data.
   - Depends on: `VIZ-02`
   - Status: `done`
4. `VIZ-04` Topology pane
   - Scope: render nodes/links with selected-event highlighting and legend.
   - Done when: selecting events updates highlighted topology state.
   - Depends on: `VIZ-03`
   - Status: `done`
5. `VIZ-05` Packet decode pane
   - Scope: render RFC-like field/value view for selected packet and protocol layer.
   - Done when: field tree updates on event select and handles missing fields gracefully.
   - Depends on: `VIZ-03`
   - Status: `done`
6. `VIZ-06` Timeline scrubber
   - Scope: implement scrub/play/pause controls and event index synchronization.
   - Done when: timeline position and selected event stay consistent during manual scrub and playback.
   - Depends on: `VIZ-03`
   - Status: `done`
7. `VIZ-07` Filter pipeline
   - Scope: add node, layer, and packet-type filters with combined predicate logic.
   - Done when: filtered timeline/event list is deterministic and reversible.
   - Depends on: `VIZ-04`, `VIZ-05`, `VIZ-06`
   - Status: `done`
8. `VIZ-08` Contract and regression tests
   - Scope: add CLI contract test for artifact generation and one deterministic fixture test for normalized schema.
   - Done when: tests run in CI and fail on schema drift.
   - Depends on: `VIZ-01`, `VIZ-02`, `VIZ-03`
   - Status: `done`
9. `VIZ-09` Docs quickstart and troubleshooting
   - Scope: document command usage, output structure, common failures, and recovery steps.
   - Done when: README/docs can be followed from clean checkout to working viewer.
   - Depends on: `VIZ-08`
   - Status: `done`

### Sprint 2: Scenario Engine (March 23 to April 12, 2026)

Status: `done`

Deliverables:

- Add scenario execution command group:
  - `pycie scenario run <scenario-file>`
  - optional report export (`--report <json|md>`)
- Support action scheduling (fail/recover events) with deterministic ordering.
- Support expected convergence assertions and structured failure reports.

Acceptance criteria:

- Scenario run returns non-zero exit status on failed expectations.
- At least two canonical scenario fixtures pass in CI.
- Failure output includes actionable reason + selector context.

### Sprint 3: Protocol Depth A (April 13 to May 3, 2026)

Status: `done`

Deliverables:

- Implement `lab17_bgp_fsm_transport`.
- Implement `lab18_ospf_multi_area`.
- Add full README guidance, capabilities wiring, exercise tests, and edge-case tests.

Acceptance criteria:

- Both labs are runnable via `pycie run lab17` and `pycie run lab18`.
- Both have deterministic exercise and edge-case coverage.
- Existing lab suites remain green.

### Sprint 4: Protocol Depth B (May 4 to May 24, 2026)

Status: `done`

Deliverables:

- Implement `lab19_ikev2_for_ipsec`.
- Implement `lab20_ipv6_nd_forwarding`.
- Implement `lab21_nat44_pipeline`.
- Add lab docs, capabilities, exercise tests, and edge-case tests.

Acceptance criteria:

- All three labs are runnable through CLI and pytest markers.
- Basic scenario coverage exists for at least one integration path (IPsec or NAT).
- No regressions in existing exercise suites.

### Cross-cutting track: Pedagogy and UX (May 11 to May 24, 2026)

Status: `planned`

Deliverables:

- Add failure explainer command:
  - `pycie explain <failed-test-or-lab>`
- Add per-lab metadata for:
  - advanced challenge flags
  - prerequisite hints

Acceptance criteria:

- Explain command maps common failures to remediation hints.
- Lab docs/CLI surface prerequisite and challenge metadata consistently.

## Highest ROI Order (if scope must be reduced)

1. `viz web` experience.
2. Scenario/failure story tooling.
3. `lab17` + `lab18`.
4. `lab19` + `lab20`.

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
