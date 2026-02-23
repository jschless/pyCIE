# Lab 18: OSPF Multi-Area ABR

## Goal

Implement multi-area OSPF behavior with area-partitioned LSDBs, ABR summary origination, and deterministic intra-area vs inter-area route selection.

## Standards references

- OSPFv2 core spec (area and summary behavior): RFC 2328 — https://datatracker.ietf.org/doc/html/rfc2328
- OSPF area design considerations: RFC 3509 — https://datatracker.ietf.org/doc/html/rfc3509
- OSPF operational guidance (context): RFC 6860 — https://datatracker.ietf.org/doc/html/rfc6860

## Files to implement

- `src/pycie/protocols/ospf_multi_area.py`
  - `OSPFMultiAreaProcess.install_area_lsa`
  - `OSPFMultiAreaProcess.install_summary_lsa`
  - `OSPFMultiAreaProcess.compute_intra_area_routes`
  - `OSPFMultiAreaProcess.originate_summaries_for_target`
  - `OSPFMultiAreaProcess.run_abr`
  - `OSPFMultiAreaProcess.compute_routing_table`
  - `OSPFMultiAreaProcess.on_frame`

## Implementation hints

- Keep LSDB state partitioned per area to avoid accidental route leakage.
- Sequence handling should accept only newer LSAs.
- For summary origination, enforce backbone transit rules:
  - non-backbone to non-backbone should not summarize directly
  - summaries should flow through area 0
- Route preference should be deterministic:
  - intra-area over inter-area for same prefix
  - then lowest cost
  - then stable tie-breaker (router-id / next-hop lexicographic)

## Step-by-step implementation plan

1. Run the lab once:

```bash
pytest -m "lab18 and exercise"
```

2. Implement LSA installation and sequence checks.
   - area LSAs keyed by `(advertising_router, prefix)` within each area.
   - summary LSAs keyed by `(advertising_router, prefix, from_area)` per target area.

3. Implement `compute_intra_area_routes`.
   - Build best route per prefix using area-local LSDB only.

4. Implement ABR summary origination.
   - Generate summaries only when process is attached to more than one area.
   - Do not import prefixes into an area when that prefix is already intra-area there.

5. Implement `compute_routing_table`.
   - Start from intra-area routes.
   - Add inter-area summaries only for missing prefixes or better inter-area tie-breaks.
   - Keep intra-area routes preferred.

6. Wire `on_frame` payload dispatch for `AreaPrefixLSA` and `SummaryLSA`.

7. Re-run:

```bash
pytest -m "lab18 and exercise"
```

## Fast feedback commands

```bash
pytest tests/labs/test_lab18_ospf_multi_area.py -k abr -q
pytest tests/labs/test_lab18_ospf_multi_area.py -k routing_table -q
pytest tests/labs/test_lab18_ospf_multi_area_edge_cases.py -k summary -q
pytest tests/labs/test_lab18_ospf_multi_area_edge_cases.py -k frame -q
```

## Common mistakes

- Mixing LSAs from different areas into one route computation.
- Replacing LSAs on equal sequence instead of only newer sequence.
- Originating summaries between two non-backbone areas directly.
- Preferring lower-cost inter-area over intra-area for the same prefix.

## Simplifications

- No DR/BDR election.
- No full LSA type matrix beyond area-prefix and summary abstractions.
- No SPF graph build from interface-level links in this lab.
- No OSPF authentication or packet-level wire format parsing.

## Tests

```bash
pytest -m "lab18 and exercise"
```

## Exit criteria

- ABR generates deterministic summary LSAs where allowed.
- Area isolation is preserved for non-backbone-only topologies.
- Route selection prefers intra-area routes and resolves summary ties deterministically.
