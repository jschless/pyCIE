# Chapter 4: Transport, NAT, ACL, and QoS

## Why this chapter matters

Policy and service behavior depends on transport metadata and deterministic rule order.

## Labs

- `lab06b_tcp_udp_fundamentals`
- `lab21_nat44_pipeline`
- `lab31_acl_filtering`
- `lab27_qos_marking_queueing`

## Concepts to master

- TCP/UDP tuple extraction
- Stateful translation and return-path validation
- First-match ACL semantics and implicit deny
- DSCP classification, queue admission, and scheduling fairness

## Hands-on sequence

```bash
pycie run lab21
pycie run lab31
pycie run lab27
```

## Checkpoint

You should be able to trace one packet through classification, policy, translation, and queueing decisions without ambiguity.
