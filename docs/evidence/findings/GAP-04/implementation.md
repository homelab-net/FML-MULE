# GAP-04 implementation record

**Finding:** GAP-04, make configuration resolution target-aware (P0).
**Controlling ADR:** FML-ADR-075. **Evidence tier:** SIMULATED.

## Defect corrected

`tools/gen-config.py` checked, emitted and validated **every** bearer target
unconditionally. The ROADMAP v0.0.1 node is access-point only, so its HaLow,
LoRa and mesh values are legitimately `TBD`; generation refused on those before
it could resolve the one target the milestone needs. The first-milestone node
could not generate its own configuration. Which bearers a node fields was
declared nowhere.

## Changes

- New node-descriptor family under `nodes/` (`README.md`, `_template/node.yml`,
  `mule-v001/node.yml`). A node declares its `active_bearers`; the v0.0.1 node
  fields `{wifi_ap}`.
- `tools/gen-config.py`: `load_node` and `active_targets` (an unknown active
  bearer is a hard error, not a silent skip); `resolve`, `validate` and
  `generate` scope to the active set; a new optional `--node` argument. Omitting
  a node preserves the whole-catalogue behaviour, so existing callers are
  unchanged.
- `active` and `required` are kept distinct: `bearers.REQUIRED_BEARERS` is not
  derived from the active set (fielding a bearer does not make its absence a
  fault).

## Scope

RF configuration only. Ingress, DNS and service configuration for v0.0.1 are not
modelled by `gen-config` and are a separate finding, not folded in here.

## Failing-first demonstration

Defeating the scoping (forcing `resolve` to all targets) makes the behavioural
tests fail:

- `test_an_ap_only_node_emits_only_its_bearer_blocks` finds a `halow` block that
  should not be emitted.
- `test_an_ap_only_node_refuses_only_on_the_trade_for_its_own_bearer` sees the
  HaLow/LoRa trade named in a refusal that should mention only `TBR-RF-03`.

## Reproduce

`python -m pytest test/unit test/flatsat` (308 tests). SIMULATED; the `TBR-RF-*`
trades still owe the real channel and power values, so a real profile still
refuses -- correctly -- until they close.
