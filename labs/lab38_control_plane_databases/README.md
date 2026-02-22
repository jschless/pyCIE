# Lab 38: Control-Plane Databases

## Goal

Model protocol-native databases explicitly (OSPF LSDB, BGP Adj-RIB-In/Loc-RIB, LDP label DB).

## Standards references

- OSPFv2: RFC 2328 — https://datatracker.ietf.org/doc/html/rfc2328
- BGP-4: RFC 4271 — https://datatracker.ietf.org/doc/html/rfc4271
- LDP: RFC 5036 — https://datatracker.ietf.org/doc/html/rfc5036

## Files to implement

- `src/pycie/protocols/control_plane_db.py`
  - `OSPFLSDB.install`
  - `OSPFLSDB.withdraw`
  - `BGPDatabase.install_path`
  - `BGPDatabase.withdraw_path`
  - `BGPDatabase.best_path`
  - `BGPDatabase.recompute_loc_rib`
  - `LDPDatabase.install_binding`
  - `LDPDatabase.withdraw_binding`
  - `LDPDatabase.best_binding`

## Step-by-step implementation

1. Implement OSPF LSDB versioning behavior.
2. Implement BGP Adj-RIB-In storage and Loc-RIB recompute.
3. Implement LDP binding database behavior.
4. Add deterministic tie-breaks for each DB.
5. Run tests: `pytest -m "lab38 and exercise"`.

## Advanced extensions

- Add explicit database change journals for explainability.
- Add aging/expiry semantics per protocol DB.
- Add protocol-specific consistency checks.

## Simplifications

- No packet parser/wire format state.
- No transport/session state in this lab.

## Tests

```bash
pytest -m "lab38 and exercise"
```

## Exit criteria

- Newer state replaces older state correctly.
- Per-protocol best selection is deterministic.
- Withdraw behavior updates derived views.
