# Chapter 7: Services and Operations

## Why this chapter matters

Network reliability depends on host services and operational visibility, not only forwarding and control-plane routing.

## Labs

- `lab28_dhcpv6_services`
- `lab33_dhcp_services`
- `lab32_aaa_access_control`
- `lab40_fhrp_gateway_redundancy`
- `lab41_management_plane_observability`

## Concepts to master

- Address-service allocation and lease lifecycle behavior
- Authentication/authorization control points
- First-hop gateway failover and preemption tradeoffs
- Management-plane telemetry and readiness dependencies

## Hands-on sequence

```bash
pycie run lab28 --student-src dist/student/src
pycie run lab33 --student-src dist/student/src
pycie run lab32 --student-src dist/student/src
pycie run lab40 --student-src dist/student/src
pycie run lab41 --student-src dist/student/src
```

## Checkpoint

You should be able to explain why a service is unavailable by tracing address allocation, gateway role, access policy, and observability signals in one path.

## Chapter navigation

<div class="chapter-nav">
  <a href="../">Course Map</a>
  <a href="../ch06_overlays_and_security/">Previous: Chapter 6</a>
</div>
