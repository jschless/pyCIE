# Lab 25: PMTUD and MSS

## Goal

Implement path-MTU learning and TCP SYN MSS clamping for constrained forwarding paths.

## Standards references

- Path MTU Discovery: RFC 1191 — https://datatracker.ietf.org/doc/html/rfc1191
- Packetization Layer PMTUD (context): RFC 4821 — https://datatracker.ietf.org/doc/html/rfc4821
- TCP specification: RFC 9293 — https://datatracker.ietf.org/doc/html/rfc9293

## Files to implement

- `src/pycie/protocols/pmtud_mss.py`
  - `PMTUDMSSProcess.evaluate_forward`
  - `PMTUDMSSProcess.learn_path_mtu`
  - `PMTUDMSSProcess.effective_path_mtu`
  - `PMTUDMSSProcess.clamp_syn_mss`
  - `PMTUDMSSProcess.age_path_mtu_cache`

## Step-by-step implementation

1. Implement DF + egress MTU evaluation and fragmentation-needed outcomes.
2. Implement PMTU cache update/lookup logic.
3. Implement SYN MSS clamping based on effective path MTU.
4. Implement PMTU cache aging.
5. Run tests: `pytest -m "lab25 and exercise"`.

## Simplifications

- No actual ICMP emission in this module.
- Single cache key model by `(src_ip, dst_ip)`.
- No PMTU probing increases in this baseline lab.

## Tests

```bash
pytest -m "lab25 and exercise"
```

## Exit criteria

- Oversized DF packets produce fragmentation-needed decisions.
- PMTU cache is deterministic and age-aware.
- SYN MSS is clamped correctly for learned path constraints.

