# TODO

This file tracks high-impact product tasks for pyCIE.

## 1) Out-of-the-box packet journey visualization

Goal: any user at any lab stage can run one command and get a machine-readable end-to-end packet trace without writing custom visualization code.

### Phase A: Trace MVP (estimated 4-6 days)

- [ ] Define `TraceEvent` schema (`time_ms`, `node`, `stage`, `action`, `packet_id`, `details`).
- [ ] Add trace collector to simulator/device path (`sim`, `core.node`).
- [ ] Emit events from forwarding stages (`l2`, `l3`, encapsulation, MPLS).
- [ ] Write JSON traces to `artifacts/traces/<run>.json`.
- [ ] Add baseline tests for deterministic trace ordering.

### Phase B: Cross-lab coverage (estimated 8-12 days total incl. Phase A)

- [ ] Add adapters for logic-first labs (`lab30`-`lab33`, `lab36`-`lab39`) so they produce trace events.
- [ ] Normalize drop/forward reason vocabulary across labs.
- [ ] Add trace-level regression tests (golden fixtures).
- [ ] Add one command to run a lab and emit trace output automatically.

### Phase C: Visualization rendering (estimated +3-7 days)

- [ ] Add renderer for Mermaid sequence diagrams and timeline summary.
- [ ] Add CLI filters (`--node`, `--packet-id`, `--stage`).
- [ ] Add sample outputs in docs.

## 2) Product docs and onboarding

Goal: make pyCIE self-explanatory to software engineers using GitHub only.

- [x] Rewrite `README.md` for audience, value, and fast-start path.
- [x] Add dedicated usage guide at `docs/usage.md`.
- [x] Add first-class CLI entrypoint (`pycie`) for discover/run flows.
- [ ] Add short architecture diagram for data/control path interactions.
- [ ] Add "how to contribute a new lab" section.

## 3) CLI polish and UX

Goal: users can discover, run, and navigate labs without knowing repo internals.

- [x] Add `pycie labs`, `pycie show`, `pycie run`, `pycie check`, `pycie guide`, `pycie quickstart`.
- [ ] Add `pycie run --trace` after trace MVP lands.
- [ ] Add `pycie run --student-src <path>` for scaffold workflows.
- [ ] Add richer output formatting (pass/fail summary and next action hints).
- [ ] Add shell completion script generation.

## 4) Metadata consistency (debt prevention)

Goal: reduce duplicated lab metadata changes across files.

- [ ] Introduce `labs/catalog.json` as source-of-truth for lab metadata.
- [ ] Generate/validate marker, capabilities, and guide indexes from catalog.
- [ ] Add CI check that catalog and markers/capabilities stay aligned.
