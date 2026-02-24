# Tutorial Course Map

This tutorial is structured as a textbook path, not a command reference.

Each chapter maps to concrete labs and expected outcomes.

```{toctree}
:maxdepth: 1
:hidden:

ch01_packet_construction
ch02_switching_and_stp
ch03_l3_and_addressing
ch04_transport_nat_acl_qos
ch05_control_plane_depth
ch06_overlays_and_security
```

<div class="link-grid">
  <a class="link-card" href="ch01_packet_construction/">
    <strong>Chapter 1: Packet Construction</strong>
    Packet headers, stack order, and deterministic packet build rules.
  </a>
  <a class="link-card" href="ch02_switching_and_stp/">
    <strong>Chapter 2: L2 Foundations</strong>
    Switching, VLAN behavior, and STP reconvergence.
  </a>
  <a class="link-card" href="ch03_l3_and_addressing/">
    <strong>Chapter 3: L3 and Addressing</strong>
    Prefix matching, route choice, ARP/ND dependencies.
  </a>
  <a class="link-card" href="ch04_transport_nat_acl_qos/">
    <strong>Chapter 4: Transport and Policy</strong>
    NAT, ACL, and QoS building blocks.
  </a>
  <a class="link-card" href="ch05_control_plane_depth/">
    <strong>Chapter 5: Control Plane Depth</strong>
    BGP/OSPF/IS-IS internals and route database behavior.
  </a>
  <a class="link-card" href="ch06_overlays_and_security/">
    <strong>Chapter 6: Overlays and Security</strong>
    Tunnels, overlay control planes, and secure transport.
  </a>
</div>

## Linear Sequence

1. [Chapter 1: Packet Construction](ch01_packet_construction)
2. [Chapter 2: Switching and STP](ch02_switching_and_stp)
3. [Chapter 3: L3 Forwarding and Addressing](ch03_l3_and_addressing)
4. [Chapter 4: Transport, NAT, ACL, and QoS](ch04_transport_nat_acl_qos)

## Part II - Control Plane and Scale

5. [Chapter 5: Control Plane Depth](ch05_control_plane_depth)
6. [Chapter 6: Overlays and Security](ch06_overlays_and_security)

## How to use each chapter

1. Read the chapter goals and mental model.
2. Implement the mapped labs in order.
3. Run exercise tests and edge-case tests.
4. Capture a trace and explain one failure/reconvergence behavior.

## Suggested pacing

- Foundations (Part I): 2-4 weeks part-time
- Part II depth tracks: 3-6 weeks depending on prior experience

## Quick Links

- New to the repo: [Start Here](../getting_started)
- CLI and workflows: [Usage Guide](../usage)
