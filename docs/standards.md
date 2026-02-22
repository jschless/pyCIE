# Standards and RFC References

The labs use simplified protocol behavior while grounding design in real standards.

## Layer 2 switching / bridging

- IEEE 802.1D (Bridging, STP)
  - https://standards.ieee.org/ieee/802.1D/7020/
- IEEE 802.1w (RSTP, now folded into 802.1D revisions)
  - https://standards.ieee.org/ieee/802.1w/11858/
- IEEE 802.1Q (VLAN bridging)
  - https://standards.ieee.org/ieee/802.1Q/7283/

Note: IEEE standards pages are linked for normative reference. The workbook uses simplified behavior models.

## Ethernet, IPv4, and ARP fundamentals

- Ethernet II encapsulation guidance: RFC 894
  - https://datatracker.ietf.org/doc/html/rfc894
- IPv4 core: RFC 791
  - https://datatracker.ietf.org/doc/html/rfc791
- ARP: RFC 826
  - https://datatracker.ietf.org/doc/html/rfc826

## OSPF

- OSPFv2: RFC 2328
  - https://datatracker.ietf.org/doc/html/rfc2328
- OSPF graceful restart notes (optional reading): RFC 3623
  - https://datatracker.ietf.org/doc/html/rfc3623

## BGP

- BGP-4 core: RFC 4271
  - https://datatracker.ietf.org/doc/html/rfc4271
- Route Reflection: RFC 4456
  - https://datatracker.ietf.org/doc/html/rfc4456
- Multiprotocol extensions (optional): RFC 4760
  - https://datatracker.ietf.org/doc/html/rfc4760

## MPLS / LDP

- MPLS architecture: RFC 3031
  - https://datatracker.ietf.org/doc/html/rfc3031
- LDP specification: RFC 5036
  - https://datatracker.ietf.org/doc/html/rfc5036
- MPLS label stack encoding: RFC 3032
  - https://datatracker.ietf.org/doc/html/rfc3032

## BFD

- BFD base: RFC 5880
  - https://datatracker.ietf.org/doc/html/rfc5880
- BFD for single-hop paths: RFC 5881
  - https://datatracker.ietf.org/doc/html/rfc5881
- BFD multipoint considerations (optional): RFC 8562
  - https://datatracker.ietf.org/doc/html/rfc8562

## Tunnels and secure encapsulation

- GRE: RFC 2784
  - https://datatracker.ietf.org/doc/html/rfc2784
- GRE key/sequence extensions: RFC 2890
  - https://datatracker.ietf.org/doc/html/rfc2890
- IP-in-IP encapsulation: RFC 2003
  - https://datatracker.ietf.org/doc/html/rfc2003
- IPsec architecture: RFC 4301
  - https://datatracker.ietf.org/doc/html/rfc4301
- ESP: RFC 4303
  - https://datatracker.ietf.org/doc/html/rfc4303

## Policy and VPN references

- BGP communities: RFC 1997
  - https://datatracker.ietf.org/doc/html/rfc1997
- BGP/MPLS IP VPNs (VRF concepts): RFC 4364
  - https://datatracker.ietf.org/doc/html/rfc4364

## Routing behavior references

- Requirements for IPv4 routers: RFC 1812 (legacy but still useful)
  - https://datatracker.ietf.org/doc/html/rfc1812
- CIDR and route aggregation background: RFC 4632
  - https://datatracker.ietf.org/doc/html/rfc4632
