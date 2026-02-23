# Lab 17: BGP FSM Transport Lifecycle

## Goal

Implement a deterministic BGP session finite-state machine with transport-up/down handling, OPEN/KEEPALIVE/UPDATE flows, timer behavior, and reset semantics.

## Standards references

- BGP-4 finite-state machine and message processing: RFC 4271 — https://datatracker.ietf.org/doc/html/rfc4271
- BGP error handling context: RFC 7606 — https://datatracker.ietf.org/doc/html/rfc7606
- BGP operational behavior context: RFC 7454 — https://datatracker.ietf.org/doc/html/rfc7454

## Files to implement

- `src/pycie/protocols/bgp_fsm_transport.py`
  - `BGPTransportSession.start`
  - `BGPTransportSession.on_tcp_up`
  - `BGPTransportSession.on_tcp_down`
  - `BGPTransportSession.receive_open`
  - `BGPTransportSession.receive_keepalive`
  - `BGPTransportSession.receive_update`
  - `BGPTransportSession.receive_notification`
  - `BGPTransportSession.tick`
  - `BGPTransportSession.inject_malformed_message`

## Implementation hints

- Keep state transitions explicit and guarded by current state checks.
- Reset behavior should be deterministic:
  - move to `IDLE`
  - clear timers
  - clear per-peer learned routes (`adj_rib_in`)
- Hold/keepalive timer math should not depend on wall-clock time.
- For predictable tests, normalize outbound behavior:
  - one OPEN on TCP-up
  - one KEEPALIVE when OPEN is accepted
  - periodic KEEPALIVE on `tick(...)` in `ESTABLISHED`

## Step-by-step implementation plan

1. Run the full lab first:

```bash
pytest -m "lab17 and exercise"
```

2. Implement startup and transport transitions.
   - `start`: `IDLE -> CONNECT`
   - `on_tcp_up`: `CONNECT -> OPENSENT`, emit OPEN
   - `on_tcp_down`: reset to `IDLE`

3. Implement OPEN validation.
   - Reject peer-AS mismatch.
   - Reject unacceptable hold-time.
   - On success: set negotiated hold/keepalive values and move to `OPENCONFIRM`.

4. Implement KEEPALIVE handling.
   - `OPENCONFIRM + KEEPALIVE -> ESTABLISHED`
   - In `ESTABLISHED`, KEEPALIVE refreshes hold timer.

5. Implement UPDATE handling.
   - Accept only in `ESTABLISHED`.
   - Install/withdraw prefixes in `adj_rib_in`.
   - Reject malformed prefix format.

6. Implement timer behavior in `tick`.
   - Generate periodic KEEPALIVE in `ESTABLISHED`.
   - Reset session on hold-timer expiry.

7. Re-run:

```bash
pytest -m "lab17 and exercise"
```

## Fast feedback commands

```bash
pytest tests/labs/test_lab17_bgp_fsm_transport.py -k handshake -q
pytest tests/labs/test_lab17_bgp_fsm_transport.py -k timer -q
pytest tests/labs/test_lab17_bgp_fsm_transport_edge_cases.py -k open -q
pytest tests/labs/test_lab17_bgp_fsm_transport_edge_cases.py -k update -q
```

## Common mistakes

- Allowing UPDATE before `ESTABLISHED`.
- Not resetting `adj_rib_in` on session reset.
- Forgetting to reset hold timer when KEEPALIVE/UPDATE is received.
- Using nondeterministic timer behavior in `tick`.
- Treating malformed messages as no-op instead of reset.

## Simplifications

- No full TCP transport stack.
- No capability negotiation or route-refresh.
- No path attributes beyond prefix/next-hop/withdraw.
- One session object per peer (no route-reflector behavior here).

## Tests

```bash
pytest -m "lab17 and exercise"
```

## Exit criteria

- OPEN/KEEPALIVE/UPDATE/NOTIFICATION transitions are deterministic.
- Hold/keepalive timers drive expected session behavior.
- Malformed input and transport-down events reset session cleanly.
