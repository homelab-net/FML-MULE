---
id: FML-ADR-075
title: A node's active bearer set is declared node data and scopes which configuration targets must resolve
status: SELECTED
date: 2026-09-11
supersedes: none
superseded-by: none
trades: [TBR-RF-01, TBR-RF-02, TBR-RF-03]
verification: SIMULATED
---

# FML-ADR-075 A node's active bearer set is declared node data and scopes which configuration targets must resolve

## Context

`tools/gen-config.py` resolves radio parameters from a region profile. It refuses
to generate when a required value is still `TBD`, which is correct: a plausible
default here becomes a fielded channel, and no value in this repository is invented.

But `unresolved()` and `resolve()` check and emit **every** bearer target
unconditionally (`halow`, `lora`, `wifi_mesh`, `wifi_ap`). The ROADMAP v0.0.1 node
is access-point only ("Conventional Wi-Fi access point only. No sub-GHz, no mesh, no
LoRa"), so its HaLow, LoRa and mesh parameters are legitimately `TBD` -- they are
bearers it does not field. Yet generation refuses on those `TBD` values before it
can resolve the one target the milestone needs. The first-milestone node cannot
generate its own configuration.

The missing fact is "which bearers does *this* node field". It is declared nowhere.
`gen-config.REQUIRED` is a static parameter catalogue for all four possible bearers,
not a per-node declaration. `mule/bearers.py:REQUIRED_BEARERS` is the set the node
cannot work *without* -- required, which is not the same as fielded.

Two homes for the missing declaration were considered: a shared code constant in
`mule/`, and a data descriptor read like a region profile. Which bearers a physical
box carries is hardware data that varies per deployment, not a decision compiled into
the node, so it belongs in data, the same place a region's channel plan lives.

## Decision

A node's **active bearer set** -- the bearers it fields -- **shall** be declared as
node data, in a per-node descriptor under `nodes/<id>/node.yml`, and **shall** scope
which configuration targets `gen-config` resolves, validates and emits.

- Resolution **shall** require only the active bearers' parameters. A `TBD` on an
  active bearer still refuses (unchanged); a `TBD` on a bearer the node does not field
  is not an error and its parameter block is not emitted.
- An active bearer that is not a known configuration target **shall** be a hard error,
  not a silent skip.
- `active` and `required` remain distinct: `bearers.REQUIRED_BEARERS` **shall not** be
  derived from the active set. A node may field a bearer it does not require; fielding
  a bearer **shall not** make its absence a fault.
- Region identity remains required for any generation, unchanged.

The v0.0.1 node's active set is `{wifi_ap}`.

## Status

SELECTED. This makes RF configuration target-aware. It does **not** model ingress,
DNS or service configuration, which the v0.0.1 milestone also needs and
`gen-config.REQUIRED` does not carry; that is a separate finding, not folded in here.

## Consequences

- The AP-only node resolves configuration with HaLow/LoRa/mesh still `TBD`, unblocking
  the first milestone.
- `gen-config` gains a `--node` input and a small `nodes/` descriptor family
  (`_template`, one real v0.0.1 node). `tools/` reading node data is consistent with
  it already reading region and mission data.
- Emitted `parameters.json` no longer carries parameter blocks for bearers a node does
  not field, so downstream template rendering must key off the active set too.
- What becomes harder: two data inputs now shape generation (region and node), so a
  wrong active-bearer declaration is a new way to get wrong output -- mitigated by the
  hard error on an unknown active bearer.

## Accepted cost

A new per-node data file is one more artefact a builder must get right, and one more
thing that can disagree with the physical hardware. The program accepts this because
the alternative -- inferring fitment from the region profile or the mission -- either
conflates "permitted in region" with "fitted on node", or puts a hardware fact in
mission data. Someone may later argue fitment should be auto-detected from enumeration
rather than declared; that is deferred to when a node can enumerate its own radios.

## Fallback

Reversible. The active set is data; if the descriptor proves the wrong shape, a later
ADR can move the declaration (for example to enumeration-derived fitment) without
changing the resolution logic, which only consumes "the list of active targets".

## Superseded by

None.

## Verification dependency

The unit tests in `test/unit/test_gen_config.py`: a v0.0.1 node resolves with all
non-AP bearer values `TBD`; an active bearer left `TBD` still refuses; an active
bearer that is not a known target raises. SIMULATED; the `TBR-RF-*` trades still owe
the real channel and power values.
