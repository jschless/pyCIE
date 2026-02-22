# Lab 01: Learning Switch

## Goal

Implement source MAC learning, destination lookup, flooding, and MAC aging behavior.

## Standards references

- IEEE 802.1D (bridge behavior): https://standards.ieee.org/ieee/802.1D/7020/
- Ethernet forwarding background: https://datatracker.ietf.org/doc/html/rfc894

## Files to implement

- `src/pycie/protocols/switching.py`
  - `LearningSwitch.on_frame`
  - `LearningSwitch.learn_source_mac`
  - `LearningSwitch.lookup_egress_interfaces`
  - `LearningSwitch.age_mac_table`
  - `LearningSwitch.should_flood`

## Implementation hints

- Interface inventory is available at `self.device.interfaces`.
  - Use `sorted(self.device.interfaces)` when you need deterministic flood order.
- Current simulation time is `self.now_ms` (milliseconds).
  - Use this for MAC learning timestamps and aging.
- Send frames with `self.device.send_frame(egress_if, frame)`.
- Typical `on_frame` order:
  1. age table
  2. learn source MAC
  3. compute egress list
  4. send on each egress

## Step-by-step implementation plan

1. Run the full lab once to see baseline failures:

```bash
pytest -m "lab01 and exercise"
```

2. Implement `should_flood`.
   - Return `True` for broadcast destination (`ff:ff:ff:ff:ff:ff`).
   - Return `True` for unknown unicast (destination missing from `self.mac_table`).
   - Return `False` for known unicast.

3. Implement `learn_source_mac`.
   - Insert/update `self.mac_table[src_mac]` with:
     - `interface=ingress_if`
     - `learned_at_ms=self.now_ms`

4. Implement `age_mac_table`.
   - Remove entries where `self.now_ms - learned_at_ms >= self.mac_aging_ms`.

5. Implement `lookup_egress_interfaces`.
   - If flooding: return all local interfaces except ingress.
   - If known unicast:
     - return `[learned_if]` if learned interface is different from ingress.
     - return `[]` if learned interface equals ingress.

6. Implement `on_frame`.
   - Call `age_mac_table`.
   - Learn source MAC.
   - Compute egress interfaces.
   - Send the frame on each egress with `self.device.send_frame(...)`.

7. Re-run full lab tests:

```bash
pytest -m "lab01 and exercise"
```

## Fast feedback commands

Use these while implementing:

```bash
pytest tests/labs/test_lab01_switching.py -k should_flood -q
pytest tests/labs/test_lab01_switching.py -k learn_source_mac -q
pytest tests/labs/test_lab01_switching.py -k age_mac_table -q
pytest tests/labs/test_lab01_switching.py -k lookup -q
```

## Common mistakes

- Forgetting to exclude ingress interface during flooding.
- Using `>` instead of `>=` in MAC aging checks.
- Not lowercasing destination MAC before broadcast comparison.
- Returning nondeterministic interface order in flood results.

## Simplifications

- No VLAN support.
- No port security.
- No MAC move dampening.

## Tests

```bash
pytest -m "lab01 and exercise"
```

## Exit criteria

- Unknown unicast floods correctly.
- Known unicast forwards to exactly one egress interface.
- MAC entries age out by timer.
