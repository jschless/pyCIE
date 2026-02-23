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
pycie run lab11
pycie run lab12
pycie run lab19
pycie run lab35
pycie run lab36
pycie run lab37
```

## Checkpoint

You should be able to explain packet identity across encapsulation layers and identify where security or overlay policy caused a drop.
