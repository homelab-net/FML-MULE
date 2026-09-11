# Nodes

**A node's active bearer set is node data, not a constant.**

Which radios a physical MULE carries varies per build. That fact -- the node's
**active bearer set** -- is declared here, as node data, the same way a region's
channel plan is declared under `regions/`. It is an **input to configuration
generation**: `tools/gen-config.py --node <id>` resolves, validates and emits
only the configuration targets for the bearers a node actually fields, so a
value that is still `TBD` for a bearer the node does not field is not a blocker.
See `FML-ADR-075`.

This is deliberately distinct from `mule/bearers.py:REQUIRED_BEARERS`, which is
the set a node cannot work *without* -- required, not fielded. A node may field
a bearer it does not require; fielding one does not make its absence a fault.

## What a node descriptor holds

| File | Contents |
| --- | --- |
| `node.yml` | The node id and its `active_bearers` list, consumed by configuration generation. |

Each active bearer names a configuration target (`halow`, `lora`, `wifi_mesh`,
`wifi_ap`). An active bearer that is not a known target is a hard error, not a
silent skip.

## Nodes in this directory

| Directory | What it is |
| --- | --- |
| `_template/` | The starting point for a new node descriptor. Copy it, do not edit it in place. |
| `mule-v001/` | The ROADMAP v0.0.1 node: a conventional Wi-Fi access point only. |
