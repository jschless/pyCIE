# Pedagogical Lab Overview

This workbook is intentionally pedagogical. The goal is not perfect router emulation.
The goal is to build durable mental models for control-plane and data-plane behavior
by implementing deterministic protocol logic in code.

## Simplification vs Fidelity

pyCIE is explicit about what is router-faithful versus intentionally reduced:

- Router-faithful focus:
  - deterministic tie-break and selection behavior
  - explicit state transitions and timer/aging outcomes
  - clear forward/drop/advertise decisions with reasons
- Intentionally simplified focus:
  - reduced protocol surfaces in some labs (staged realism)
  - simplified signaling/wire behavior where the learning target is decision logic
  - compact scenario actions for controlled failure exercises

Use this rule: trust the decision process and state transitions as the core learning
artifact; treat omitted protocol surface area as planned scaffolding, not full-device
emulation.

## How To Read Implementation Steps

When a lab asks you to implement a method, use this consistent lens:

1. Parse and validate inputs.
2. Build candidate decisions (routes, ports, peers, labels, policies).
3. Apply deterministic tie-break rules.
4. Commit state transitions.
5. Emit output actions (forward, flood, advertise, drop) and reasons.
6. Age timers/state and handle failure paths.

For each lab, focus on what state is authoritative, what events change it, and what
observable behavior proves your implementation is correct.

## Lab-By-Lab Intent and Steps

### `lab01` Learning Switching

- Intent: Understand MAC learning and unknown-unicast flooding.
- Implement: source MAC learning, destination lookup, flood/unicast decision, MAC aging.
- Learn: why switches are stateful and why unknown traffic fans out.

### `lab02` STP

- Intent: Prevent loops with root election and per-port roles.
- Implement: BPDU comparison, root port choice, role/state recomputation, forwarding gate.
- Learn: loop prevention as a deterministic election problem.

### `lab03` OSPF (Single Area)

- Intent: Build IGP thinking from hello/LSA to SPF output.
- Implement: neighbor transitions, LSA installation with sequence checks, SPF path selection.
- Learn: how link-state databases become routing decisions.

### `lab04` BGP

- Intent: Learn path-vector selection and Loc-RIB recompute flow.
- Implement: peer session gating, Adj-RIB-In updates, best-path tie-breakers, export filtering.
- Learn: policy-oriented route selection versus shortest-path routing.

### `lab05` LDP

- Intent: Connect FECs to labels and build MPLS forwarding views.
- Implement: local label allocation, remote mapping install, LFIB derivation.
- Learn: control-plane label signaling driving data-plane label operations.

### `lab06` BFD

- Intent: Model fast liveliness detection as a timer/state machine.
- Implement: discriminator matching, state transitions, detect-time computation, timeout handling.
- Learn: failure detection as strict timer math plus finite state.

### `lab06a` Packet Construction

- Intent: Understand packet stacks as ordered headers with validity rules.
- Implement: stack validation, IPv4+TCP/UDP builders, VLAN insertion, length normalization.
- Learn: protocol behavior starts with precise packet structure.

### `lab06b` TCP/UDP Fundamentals

- Intent: Build transport intuition from state and flags, not socket APIs.
- Implement: TCP handshake/close transitions, segment validation, 5-tuple extraction, UDP checksum.
- Learn: transport behavior is deterministic state evolution over packets.

### `lab06c` IP Subnet + MAC Forwarding Basics

- Intent: Bridge subnetting, route lookup, and adjacency resolution.
- Implement: connected/static lookup, longest-prefix decision explanation, ARP-dependent forwarding.
- Learn: routing decisions and L2 resolution are separate but coupled.

### `lab07` IPv4 Forwarding

- Intent: Implement a forwarding pipeline with clear drop/forward reasons.
- Implement: route install/withdraw, LPM lookup, TTL decrement/expiry behavior, egress selection.
- Learn: forwarding correctness is best-path plus packet mutation plus exceptions.

### `lab08` ARP

- Intent: Resolve next-hop IP to MAC and model request/reply behavior.
- Implement: ARP message parse/build, cache update, request/response logic, pending queue flow.
- Learn: L3 forwarding pauses without L2 neighbor knowledge.

### `lab09` VLAN Bridging

- Intent: Add VLAN context to L2 learning and forwarding.
- Implement: ingress VLAN classification, VLAN-aware FDB learning, tagged/untagged egress rules.
- Learn: broadcast domains are logical constructs enforced in forwarding logic.

### `lab10` RSTP

- Intent: Model rapid convergence concepts over STP foundations.
- Implement: proposal/agreement handling, role/state transitions, BPDU transmission.
- Learn: reconvergence speed comes from explicit handshake semantics.

### `lab11` GRE

- Intent: Treat tunneling as deterministic header-stack transformation.
- Implement: encapsulation and decapsulation checks for GRE-over-IPv4.
- Learn: overlays are systematic packet wrapping/unwrapping, not magic links.

### `lab12` IPsec

- Intent: Separate policy decision (SPD) from security association state (SAD).
- Implement: outbound policy match, ESP encapsulation, inbound SPI validation and decapsulation.
- Learn: security forwarding is policy + SA lifecycle + packet transforms.

### `lab13` BGP Policy

- Intent: Apply ordered match/action policy logic to route attributes.
- Implement: rule matching, action mutation, permit/deny behavior, import/export chains.
- Learn: policy pipelines are deterministic filters and transformers.

### `lab14` VRF

- Intent: Isolate routing domains and selectively leak routes.
- Implement: VRF/interface binding, per-VRF route install, RT-based route leaking.
- Learn: multi-tenancy is controlled route visibility.

### `lab15` MPLS Forwarding

- Intent: Execute LFIB-driven label push/swap/pop operations.
- Implement: LFIB lookup, label stack mutation, drop reasons for missing entries.
- Learn: MPLS forwarding is label-state orchestration, not IP lookup alone.

### `lab16` Capstone

- Intent: Combine multi-protocol behavior in failure/reconvergence stories.
- Implement: scenario action application, failure/recovery state mutation, and expectation evaluation.
- Learn: network behavior must be validated end-to-end under failure pressure.
- Detailed step focus:
  - Stage disruptions (`fail_link`, `fail_bgp_peer`) and make impact explicit (`route_set_absent`).
  - Stage restorations (`recover_link`, `recover_bgp_peer`) independently of expectations.
  - Represent completion (`route_set_present`, `mark_converged`) and assert elapsed convergence windows.
  - Treat scenario JSON as an executable incident timeline, not static test data.

### `lab17` BGP FSM + Transport

- Intent: Understand BGP session lifecycle independent of rich policy.
- Implement: OPEN/KEEPALIVE/UPDATE transitions, timers, reset/notification paths.
- Learn: route exchange depends on transport-state correctness first.

### `lab18` OSPF Multi-Area

- Intent: Move from area-local LSDB to ABR summary behavior.
- Implement: per-area LSDB/summary LSDB install, summary origination, inter/intra-area preference.
- Learn: hierarchy reduces scale but introduces route-type preference semantics.

### `lab19` IKEv2 for IPsec

- Intent: Model SA negotiation and child-SA lifecycle.
- Implement: proposal acceptance, child SA creation, rekey overlap, deletion behavior.
- Learn: secure tunnels rely on explicit key-management state transitions.

### `lab20` IPv6 ND Forwarding

- Intent: Rebuild L3 forwarding with IPv6 + neighbor discovery.
- Implement: IPv6 route lookup, neighbor cache learning/aging, pending queue and resolution.
- Learn: IPv6 forwarding combines routing and ND neighbor-state management.

### `lab21` NAT44 Pipeline

- Intent: Understand stateful translation for outbound and return traffic.
- Implement: session creation/reuse, static and dynamic inbound translation, session aging.
- Learn: NAT is bidirectional state correlation, not simple address rewrite.

### `lab22` ICMP Control-Plane Basics

- Intent: Treat diagnostics as protocol logic rather than ping commands.
- Implement: echo request/reply, unreachable/time-exceeded generation, traceroute hop outcomes.
- Learn: control-plane error messages are deterministic reactions to data-plane conditions.

### `lab23` IS-IS

- Intent: Build level-aware link-state routing logic.
- Implement: LSP origination/install, per-level SPF, level-preference route selection.
- Learn: IS-IS levels model routing scope and path choice boundaries.

### `lab24` IPv4 Fragmentation/Reassembly

- Intent: Understand MTU constraints and fragment lifecycle.
- Implement: DF checks, fragment slicing/offsets, reassembly with gap/overlap handling, timeout aging.
- Learn: fragmentation is stateful and failure-prone without strict bookkeeping.

### `lab25` PMTUD + MSS

- Intent: Learn packet-size control beyond fixed MTU assumptions.
- Implement: fragmentation-needed decisions, PMTU cache updates/aging, TCP MSS clamp logic.
- Learn: size negotiation is dynamic and path-specific.

### `lab26` IPv6 SLAAC, RA/RS, DAD

- Intent: Model host autoconfiguration and uniqueness checks.
- Implement: RA config, RS-triggered RA emission, SLAAC derivation, DAD completion/conflict.
- Learn: host addressing is a protocol workflow, not static assignment.

### `lab27` QoS Marking + Queueing

- Intent: Convert DSCP classification into queue behavior.
- Implement: classification, remarking, admission/drop, weighted dequeue scheduling.
- Learn: QoS is classification plus resource arbitration under load.

### `lab28` DHCPv6 Services

- Intent: Model deterministic lease allocation and renewal.
- Implement: SOLICIT/REQUEST handling, lease tracking, aging, relay helper behavior.
- Learn: stateful address services are identity + lease-time workflows.

### `lab29` LACP

- Intent: Build bundle membership from actor/partner state.
- Implement: partner sync logic, active-member selection, deterministic egress hashing, session aging.
- Learn: link aggregation depends on negotiated consistency, not link count alone.

### `lab30` Route Selection + Redistribution

- Intent: Normalize route-choice logic across protocols.
- Implement: candidate install/withdraw, explainable ranking, redistribution with loop-prevention tags.
- Learn: multiprotocol routing requires explicit preference and loop guards.

### `lab31` ACL Filtering

- Intent: Apply ordered packet filters with first-match semantics.
- Implement: rule matching, ordered insertion/removal, implicit deny.
- Learn: policy safety depends on evaluation order and default outcomes.

### `lab32` AAA Access Control

- Intent: Separate authentication, authorization, and accounting concerns.
- Implement: backend/local login behavior, command-role authorization, session/logout accounting.
- Learn: access control correctness is policy plus session lifecycle.

### `lab33` DHCP Services (IPv4)

- Intent: Reinforce stateful lease behavior in IPv4 service workflows.
- Implement: discover/offer/request/ack logic, renew/release, lease expiration, relay logic.
- Learn: service reliability depends on deterministic pool-state transitions.

### `lab34` Multicast Foundations

- Intent: Model multicast forwarding as (S,G) state with RPF safety.
- Implement: group membership, RPF route lookup, egress interface computation, SG-state update.
- Learn: multicast forwarding is source-aware and strict on reverse-path checks.

### `lab35` VXLAN Data Plane

- Intent: Build overlay forwarding with VNI-scoped learning.
- Implement: local/remote MAC learning, flood/unicast lookup, VXLAN encapsulation/decapsulation.
- Learn: overlays compose L2 semantics over L3 transport.

### `lab36` EVPN Control Plane

- Intent: Control overlay reachability with route import and best-path logic.
- Implement: RT-based import, withdraw/recompute, MAC/IP route resolution.
- Learn: EVPN is policy-governed control-plane state for overlay forwarding.

### `lab37` MACsec Link Security

- Intent: Add per-link security policy and replay protection.
- Implement: policy install, SA management, ingress validation, replay window pruning, egress protection.
- Learn: link security is stateful validation, not only encryption enable/disable.

### `lab38` Control-Plane Databases

- Intent: Explicitly model OSPF/BGP/LDP databases as first-class objects.
- Implement: install/withdraw semantics, per-protocol best-path/best-binding recompute.
- Learn: protocol behavior is database lifecycle plus deterministic selection.

### `lab39` RIB-to-FIB Pipeline

- Intent: Understand why route choice and route programmability are different problems.
- Implement: per-prefix best route, next-hop recursion resolution, FIB install trace steps.
- Learn: control-plane correctness must still pass data-plane install constraints.

### `lab40` FHRP Gateway Redundancy

- Intent: Model active-gateway election and failover behavior.
- Implement: router registration, master election/preemption, failover timing markers, virtual MAC derivation.
- Learn: first-hop redundancy is deterministic election with operational timing concerns.

### `lab41` Management-Plane Observability

- Intent: Treat operations telemetry as protocol state with readiness checks.
- Implement: LLDP learning/aging, syslog filtering, SNMP OID state, DNS caching, NTP sync checks.
- Learn: operational visibility is a behavior model, not post-hoc logging only.

## Expected Outcome For Learners

After completing the sequence, a software engineer should be able to:

1. Explain forwarding and control-plane behavior as explicit state transitions.
2. Reason about tie-breakers, failure modes, and convergence timing.
3. Read packet/header transformations without relying on vendor CLI abstraction.
4. Extend protocol behavior safely by preserving deterministic decision logic.
