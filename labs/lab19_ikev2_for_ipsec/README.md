# Lab 19: IKEv2 for IPsec

## Goal

Implement a deterministic IKEv2 control-plane model that negotiates IKE SAs, establishes Child SAs, handles selector validation, and supports rekey overlap behavior.

## Standards references

- IKEv2 protocol: RFC 7296 — https://datatracker.ietf.org/doc/html/rfc7296
- Cryptographic algorithm recommendations (context): RFC 8247 — https://datatracker.ietf.org/doc/html/rfc8247
- IPsec architecture context: RFC 4301 — https://datatracker.ietf.org/doc/html/rfc4301

## Files to implement

- `src/pycie/protocols/ikev2_for_ipsec.py`
  - `IKEv2Session.initiate`
  - `IKEv2Session.respond`
  - `IKEv2Session.establish_child_sa`
  - `IKEv2Session.rekey_child_sa`
  - `IKEv2Session.age_rekey_overlap`
  - `IKEv2Session.active_child_sas`
  - `IKEv2Session.delete_session`

## Implementation hints

- Keep SA lifecycle explicit:
  - `INIT -> IKE_ESTABLISHED -> CHILD_ESTABLISHED`
  - any fatal negotiation error -> `DELETED`
- Proposal matching should be exact and deterministic.
- Child SA rekey should create a replacement SA and optionally overlap old/new SAs.
- Selector validation should fail fast with a clear `last_error`.

## Step-by-step implementation plan

1. Run the lab once:

```bash
pytest -m "lab19 and exercise"
```

2. Implement proposal negotiation.
   - Accept only proposals in `accepted_proposals`.
   - Move to `IKE_ESTABLISHED` on success.

3. Implement Child SA creation.
   - Require IKE SA already established.
   - Validate selectors.
   - Track Child SA IDs deterministically.

4. Implement rekey behavior.
   - Create replacement SA with `rekey_of` set.
   - Keep old SA active only during overlap.
   - Deactivate old SA when overlap expires.

5. Implement session delete and active-SA view.

6. Re-run:

```bash
pytest -m "lab19 and exercise"
```

## Fast feedback commands

```bash
pytest tests/labs/test_lab19_ikev2_for_ipsec.py -k proposal -q
pytest tests/labs/test_lab19_ikev2_for_ipsec.py -k rekey -q
pytest tests/labs/test_lab19_ikev2_for_ipsec_edge_cases.py -k selector -q
```

## Common mistakes

- Allowing Child SA establishment before IKE SA exists.
- Rekeying without linking replacement SA to parent (`rekey_of`).
- Forgetting to deactivate old SA after overlap timeout.
- Treating selector mismatch as success.

## Simplifications

- No full wire-format exchange or retransmission model.
- No cryptographic key derivation.
- No MOBIKE, EAP, or fragmentation support.

## Tests

```bash
pytest -m "lab19 and exercise"
```

## Exit criteria

- Negotiation success/failure paths are deterministic.
- Rekey overlap and timeout handling behave predictably.
- Selector mismatch is rejected with clear failure state.
