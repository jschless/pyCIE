# Chapter 2: L2 Foundations (Switching + STP)

## Why this chapter matters

L2 behavior determines whether frames are delivered, flooded, or looped. STP exists to keep redundant topologies safe.

## Labs

- `lab01_switching`
- `lab02_stp`
- `lab09_vlan`
- `lab10_rstp`

## Concepts to master

- MAC learning, flooding, and aging
- Broadcast domain behavior with VLAN tagging
- Root bridge election and port role/state outcomes
- Reconvergence after topology changes

## Hands-on sequence

```bash
pycie run lab01
pycie run lab02
pycie run lab09
pycie run lab10
```

For visibility:

```bash
pycie run lab02 --trace-out traces/lab02.jsonl
pycie viz stp --trace traces/lab02.jsonl
```

## Checkpoint

You should be able to explain why a given port is forwarding/blocking and how that affects packet paths.
