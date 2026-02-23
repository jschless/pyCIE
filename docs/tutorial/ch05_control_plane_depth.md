# Chapter 5: Control Plane Depth

## Why this chapter matters

Scalable network behavior depends on deterministic control-plane convergence and route database handling.

## Labs

- `lab03_ospf`
- `lab04_bgp`
- `lab17_bgp_fsm_transport`
- `lab18_ospf_multi_area`
- `lab23_isis`
- `lab38_control_plane_databases`
- `lab39_rib_to_fib_pipeline`

## Concepts to master

- Session/FSM lifecycle and timer handling
- LSA/LSP/path install and replacement rules
- Best-path versus forwarding-programming boundaries
- Explainable RIB-to-FIB transitions

## Hands-on sequence

```bash
pycie run lab17
pycie run lab18
pycie run lab23
pycie run lab38
pycie run lab39
```

## Checkpoint

You should be able to explain where a route lives at each stage (protocol DB, RIB, FIB) and what event caused each transition.
