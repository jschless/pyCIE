# CLI Visualization Plan (Packet Encapsulation + Device-to-Device Flow)

> Note: this file is historical planning context. For current commands and
> schema, use `docs/visualization.md` and `src/pycie/telemetry/events.py`.

## Goal

Build an instructive CLI visualization tool that lets students see:

1. How packets move hop-by-hop through the simulated topology.
2. How encapsulation and decapsulation change header stacks.
3. Which decisions are made at different OSI layers.

The tool should be deterministic, scriptable, and lab-friendly.

## Non-Negotiable Requirement: Zero Student Implementation

Visualization must work even if students never touch visualization code.

1. No `TODO(student)` hooks for tracing.
2. No required calls like `trace.emit(...)` in lab solutions.
3. Instrumentation lives in framework/runtime boundaries only.
4. Student code can remain focused on protocol/forwarding logic.

## Student Outcomes

A student should be able to answer:

1. "Where did this packet go, and when?"
2. "Why was it forwarded, flooded, dropped, or tunneled?"
3. "What did the packet look like at L2/L3/tunnel layers at each hop?"
4. "Which protocol/process caused this behavior?"

## Scope

### In scope (initial)

1. CLI command family under `pycie viz ...`.
2. Event tracing from simulator, device ingress/egress, and forwarding pipelines.
3. Multiple output views:
   - timeline view
   - path/hop view
   - header-stack diff view
4. OSI-layer filtering (`l2`, `l3`, `l4`, `overlay`).
5. Replay from trace file (JSONL) for post-run analysis.

### Out of scope (initial)

1. GUI/web UI.
2. PCAP byte-accurate wire encoding.
3. Real-time ncurses animation (can be phase 2+).

## Proposed Architecture

### 1) Trace Event Model

Add a telemetry package (for example: `src/pycie/telemetry/`) with:

1. `TraceEvent` dataclass:
   - `time_ms`
   - `event_type`
   - `layer`
   - `node_id`
   - `ingress_if` / `egress_if`
   - `packet_id`
   - `parent_packet_id` (for encapsulation)
   - `headers_before`
   - `headers_after`
   - `decision`
   - `reason`
2. `TraceSink` protocol/interface:
   - `emit(event)`
   - `flush()`
3. Default no-op sink to avoid overhead when tracing is disabled.

### 2) Packet Identity

Use `PacketStack.metadata` to maintain:

1. `packet_id`: stable ID for the packet instance.
2. `flow_id`: stable ID for related packets in a scenario.
3. `parent_packet_id`: set on encapsulated packets.

This enables clear lineage in GRE/IPsec/MPLS transformations.

### 3) Instrumentation Points

Hook event emission at high-value points:

1. Simulator transport:
   - `NetworkSimulator.send_frame` (enqueue, deliver, drop/loss/link-down).
2. Device receive/send boundary:
   - `Device._receive_from_sim`
   - `Device.send_frame`
3. L2 forwarding:
   - learning/flood/unicast decision in switching and bridge domain logic.
4. L3 forwarding:
   - route lookup, TTL decrement, drop reasons.
5. Encapsulation/tunnels:
   - GRE/IPsec/MPLS push/swap/pop/decap operations with stack diff.

Implementation rule:

1. Prefer boundary wrappers and framework methods over per-lab inline tracing.
2. `PacketStack` operations and simulator/device boundaries are primary signal sources.
3. If a student method is incomplete, visualization still renders available events.

### 4) Renderer Layer

Create renderers that consume `TraceEvent` streams:

1. Timeline renderer: one line per event ordered by sim time.
2. Path renderer: packet-centric hop chain.
3. Stack renderer: before/after header stack changes at each transformation.

## CLI UX Proposal

Add a project CLI entrypoint and a `viz` command group.

### Commands

1. `pycie viz run`
   - runs a lab/scenario and emits visualization in one pass.
2. `pycie viz replay`
   - re-renders from a saved trace file.
3. `pycie viz explain`
   - packet-centric narrative from trace data.

### Example invocations

```bash
pycie viz run --scenario labs/scenarios/lab16_dual_failure.json --view timeline
pycie viz run --scenario labs/scenarios/lab16_dual_failure.json --view path --packet-id p17
pycie viz run --scenario labs/scenarios/lab16_dual_failure.json --view stack --layers l2,l3,overlay
pycie viz replay --trace out/trace.jsonl --view timeline
pycie viz explain --trace out/trace.jsonl --packet-id p17
```

### Useful flags

1. `--layers l2,l3,l4,overlay`
2. `--node r1`
3. `--packet-id p17`
4. `--from-ms 0 --to-ms 500`
5. `--drop-only`
6. `--trace-out out/trace.jsonl`
7. `--no-color` (CI-safe output)

## OSI-Level Mapping

Use a practical mapping for student learning:

1. `l2`: Ethernet, VLAN, MAC learning, STP/RSTP forwarding state impact.
2. `l3`: IPv4 forwarding, ARP resolution interaction, routing outcomes.
3. `l4`: BFD keepalive/timeout and transport-level implications where modeled.
4. `overlay`: GRE, IPsec, MPLS label operations.

Each event should include both `layer` and a protocol/process tag.

## Phased Implementation Plan

## Phase 0: Design + Contracts (1-2 days)

1. Define `TraceEvent` schema and layer taxonomy.
2. Decide packet ID rules and parent-child lineage behavior.
3. Add unit tests for schema serialization and deterministic ordering.

Deliverable: telemetry contracts + tests.

Acceptance criteria for Phase 0:

1. Trace API can be enabled globally without editing lab implementations.
2. Trace API has a no-op default so existing tests and labs are unchanged.

## Phase 1: MVP Trace + Timeline (3-5 days)

1. Add trace sink plumbing to simulator/device boundaries.
2. Emit transport + basic forwarding decision events.
3. Implement `pycie viz replay --view timeline`.
4. Write JSONL sink and parser.

Deliverable: deterministic timeline visualization from saved traces.

Acceptance criteria for Phase 1:

1. A student can run visualization on existing labs with zero code modifications.
2. Hop-level path output appears even when protocol internals are partially implemented.

## Phase 2: Encapsulation-Centric Views (3-5 days)

1. Instrument GRE/IPsec/MPLS/encapsulation pipeline.
2. Implement stack diff view.
3. Implement packet lineage view (`packet_id` + `parent_packet_id`).

Deliverable: students can inspect encapsulation/decapsulation step-by-step.

## Phase 3: OSI Filters + Explanations (2-4 days)

1. Add robust `--layers` filtering.
2. Implement `viz explain` narrative mode for one packet/flow.
3. Add drop-reason summary ("why dropped?").

Deliverable: targeted, instructive debugging output by OSI layer.

## Phase 4: Lab Integration + Teaching Assets (2-4 days)

1. Add examples to lab docs (start with Lab 07, 11, 12, 15, 16).
2. Add snapshot tests for CLI outputs.
3. Add "teaching recipes" with expected traces for canonical scenarios.

Deliverable: reproducible student workflows and lab-ready docs.

## Testing Strategy

1. Unit tests:
   - event creation/serialization
   - packet ID lineage behavior
   - renderer formatting stability
2. Integration tests:
   - run representative labs and assert expected trace events.
3. Snapshot tests:
   - lock CLI output for key scenarios.
4. Regression tests:
   - ensure tracing disabled path preserves current behavior.

## Risks and Mitigations

1. Noise overload in traces.
   - Mitigation: strong default filters + concise event taxonomy.
2. Instrumentation overhead.
   - Mitigation: no-op sink by default and lightweight event payloads.
3. Ambiguous packet lineage when cloning.
   - Mitigation: explicit ID policy in one utility module with tests.
4. Divergence from pedagogical goals.
   - Mitigation: add "learning-first" views before advanced visual effects.

## Initial Feature Backlog (Recommended MVP)

1. `TraceEvent` schema + JSONL sink.
2. `packet_id` assignment utility.
3. Simulator/device boundary instrumentation.
4. Timeline renderer.
5. OSI layer filter support.
6. Stack diff renderer for tunnel labs.
7. CLI command entrypoint for `pycie viz replay`.

## Definition of Done (MVP)

1. Students can run one command and see hop-by-hop packet flow for a scenario.
2. Students can filter to OSI layers and isolate one packet.
3. Students can see header stack changes during GRE/IPsec/MPLS operations.
4. Output is deterministic and covered by tests.
