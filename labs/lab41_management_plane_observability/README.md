# Lab 41: Management-Plane Observability

## Goal

Implement baseline management-plane telemetry behavior for LLDP, syslog, SNMP, DNS, and service readiness checks.

## Standards references

- LLDP: IEEE 802.1AB — https://standards.ieee.org/ieee/802.1AB/10950/
- Syslog protocol: RFC 5424 — https://datatracker.ietf.org/doc/html/rfc5424
- SNMPv2 SMI: RFC 2578 — https://datatracker.ietf.org/doc/html/rfc2578
- DNS concepts: RFC 1034 — https://datatracker.ietf.org/doc/html/rfc1034
- NTPv4: RFC 5905 — https://datatracker.ietf.org/doc/html/rfc5905

## Files to implement

- `src/pycie/protocols/management_plane_observability.py`
  - `ManagementPlaneObservabilityProcess.learn_lldp`
  - `ManagementPlaneObservabilityProcess.age_lldp`
  - `ManagementPlaneObservabilityProcess.log_syslog`
  - `ManagementPlaneObservabilityProcess.poll_snmp_oid`
  - `ManagementPlaneObservabilityProcess.resolve_dns`
  - `ManagementPlaneObservabilityProcess.check_service_readiness`

## Step-by-step implementation

1. Implement LLDP learn/age behavior.
2. Implement syslog severity filtering.
3. Implement SNMP OID polling behavior.
4. Implement DNS cache resolution with TTL behavior.
5. Implement readiness checks over NTP sync + DNS availability.
6. Run tests: `pytest -m "lab41 and exercise"`.

## Simplifications

- No network transport of syslog/SNMP packets.
- No DNS recursion or authoritative behavior.
- No NTP discipline loop model.

## Tests

```bash
pytest -m "lab41 and exercise"
```

## Exit criteria

- Neighbor/record aging is deterministic.
- Severity filtering and lookups are reproducible.
- Readiness checks provide actionable failure reason strings.
