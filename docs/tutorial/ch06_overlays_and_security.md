# Chapter 6: Overlays and Security

## Why this chapter matters

Production networks combine encapsulation, identity, and policy layers; debugging requires understanding their interaction.

## Labs

- `lab11_gre`
- `lab12_ipsec`
- `lab19_ikev2_for_ipsec`
- `lab34_multicast_foundations`
- `lab35_vxlan_overlay_data_plane`
- `lab36_evpn_control_plane`
- `lab37_macsec_link_security`

## Concepts to master

- Tunnel encapsulation/decapsulation behavior
- Security association lifecycle and replay considerations
- Overlay control-plane versus data-plane learning
- Link-level security policy and failure modes

## Hands-on sequence

```bash
pycie run lab11 --student-src dist/student/src
pycie run lab12 --student-src dist/student/src
pycie run lab19 --student-src dist/student/src
pycie run lab35 --student-src dist/student/src
pycie run lab36 --student-src dist/student/src
pycie run lab37 --student-src dist/student/src
```

## Checkpoint

You should be able to explain packet identity across encapsulation layers and identify where security or overlay policy caused a drop.

## Chapter navigation

<div class="chapter-nav">
  <a href="../">Course Map</a>
  <a href="../ch05_control_plane_depth/">Previous: Chapter 5</a>
  <a href="../ch07_services_and_operations/">Next: Chapter 7</a>
</div>
