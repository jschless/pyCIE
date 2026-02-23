# Visualization Guide

pyCIE can emit structured JSONL traces and replay them from the CLI.

This phase-1 visualization scope covers:

- L2 switching decisions (`MAC_LEARN`, `L2_FLOOD`, `L2_UNICAST_FORWARD`, `MAC_AGE_OUT`)
- STP elections and port-role transitions
- L3 route lookup/selection/forward-drop decisions
- Encapsulation and encryption transitions (GRE/IPsec)

## Capture traces

Run labs with `--trace-out`:

```bash
pycie run lab01 --trace-out traces/lab01.jsonl
pycie run lab02 --trace-out traces/lab02.jsonl
pycie run lab07 --trace-out traces/lab07.jsonl
pycie run lab11 --trace-out traces/lab11.jsonl
pycie run lab12 --trace-out traces/lab12.jsonl
```

## Replay traces

Chronological replay with filters:

```bash
pycie viz replay --trace traces/lab01.jsonl --detail packet
pycie viz replay --trace traces/lab07.jsonl --event ROUTE_SELECT --event FIB_DROP
pycie viz replay --trace traces/lab12.jsonl --event CRYPTO_ENCRYPT --event ENCAP_PUSH
```

Packet-centric flow:

```bash
pycie viz packet --trace traces/lab11.jsonl --packet-id p1 --detail full
```

Topology snapshot and packet location:

```bash
pycie viz topology --trace traces/lab01.jsonl
pycie viz topology --trace traces/lab01.jsonl --packet-id p1
```

Time-sequence playback:

```bash
pycie viz sequence --trace traces/lab01.jsonl --packet-id p1 --detail packet
```

STP election summary:

```bash
pycie viz stp --trace traces/lab02.jsonl
pycie viz stp --trace traces/lab02.jsonl --bridge-id 32768:00:00:00:00:00:01
```

## Web viewer (offline static HTML)

Generate a browser viewer from an existing trace:

```bash
pycie viz web --trace traces/lab01.jsonl --out dist/viz/lab01
```

Then open:

```bash
dist/viz/lab01/index.html
```

The web viewer includes:

- topology pane with active-node and active-link highlighting
- timeline pane with event selection, scrubber, and play/pause playback
- packet decode pane with RFC-style field/value table and packet-tree rendering
- filters for node, layer, and packet-id

## Event schema

Every event is one JSON object with fields:

- `schema_version`: current schema version (`1`)
- `seq`: monotonic sequence number
- `ts_ms`: wall-clock timestamp in milliseconds
- `sim_time_ms`: simulation time in milliseconds
- `node`: device/logical node name
- `ingress_if` / `egress_if`: interface context when present
- `packet_id`: correlation id for packet life-of-flow
- `layer`: one of `SIM`, `L2`, `STP`, `L3`, `TUNNEL`, `CRYPTO`
- `event_type`: typed event enum (see `src/pycie/telemetry/events.py`)
- `details`: event-specific key/value payload

## Typical workflows

Understand STP election changes:

1. Run `pycie run lab02 --trace-out traces/lab02.jsonl`
2. Run `pycie viz stp --trace traces/lab02.jsonl`
3. Correlate `STP_ROOT_CHANGE` with `STP_PORT_ROLE_CHANGE`

Understand encapsulation + encryption layering:

1. Run `pycie run lab11 --trace-out traces/lab11.jsonl`
2. Run `pycie run lab12 --trace-out traces/lab12.jsonl`
3. Filter for `ENCAP_PUSH`/`ENCAP_POP` and `CRYPTO_ENCRYPT`/`CRYPTO_DECRYPT`
4. Use `pycie viz packet` for packet-by-packet path

Understand where a packet is in the topology:

1. Run `pycie run lab01 --trace-out traces/lab01.jsonl`
2. Run `pycie viz topology --trace traces/lab01.jsonl --packet-id p1`
3. Run `pycie viz sequence --trace traces/lab01.jsonl --packet-id p1`

## Design constraints

- Visualization is additive; it does not change lab semantics.
- No plaintext keys or cryptographic material are logged.
- If a protocol path is malformed, drop/failure context is logged with `FRAME_DROP` and `drop_reason`.

## Troubleshooting

1. `pycie viz web` succeeds but page looks empty
   - Confirm `data.js` exists in the output directory next to `index.html`.
   - Re-run command with a known trace: `pycie viz web --trace traces/lab01.jsonl --out dist/viz/lab01`.
2. No links appear in topology pane
   - Link discovery depends on `FRAME_ENQUEUE` events with `src_node/src_if/dst_node/dst_if`.
3. Packet decode pane lacks packet fields
   - Some events are control-path only and may not include `packet_summary` or `packet_tree`.
