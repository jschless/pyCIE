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
pycie run lab17 --student-src dist/student/src
pycie run lab18 --student-src dist/student/src
pycie run lab23 --student-src dist/student/src
pycie run lab38 --student-src dist/student/src
pycie run lab39 --student-src dist/student/src
```

## Checkpoint

You should be able to explain where a route lives at each stage (protocol DB, RIB, FIB) and what event caused each transition.

## Chapter navigation

<div class="chapter-nav">
  <a href="../">Course Map</a>
  <a href="../ch04_transport_nat_acl_qos/">Previous: Chapter 4</a>
  <a href="../ch06_overlays_and_security/">Next: Chapter 6</a>
</div>
