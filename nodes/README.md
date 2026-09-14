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
| `node.yml` | The node id, its `active_bearers` list (consumed by configuration generation), and its `interfaces` role-to-device map. |

Each active bearer names a configuration target (`halow`, `lora`, `wifi_mesh`,
`wifi_ap`). An active bearer that is not a known target is a hard error, not a
silent skip.

## Interfaces: roles, not device names

`interfaces` binds a **logical role** (`wan`, `eud_ap`, `mesh`, `halow`, `lora`)
to the concrete device that plays it on that node. Bring-up code and templates
reference the role; only this map changes between a lab bench and the field
prototype, so the lab can stand in for the prototype without code rework
(FML-ADR-045's separate-functions model). A device the node does not have is
`none`. Radios are identified by driver, never by a fuzzy name match.

This keeps the software **device-agnostic**: retasking a radio, or building a
different device on this codebase entirely, is a change to one node's interface
map, not to the code. Roles are assigned to hardware in configuration; the code
never names a device.

## Nodes in this directory

| Directory | What it is |
| --- | --- |
| `_template/` | The starting point for a new node descriptor. Copy it, do not edit it in place. |
| `mule-v001/` | The ROADMAP v0.0.1 node: a conventional Wi-Fi access point only. |
| `lab-bench/` | The development-machine bench standing in for the prototype; its substitutions are recorded in `docs/dev-machine.md`. |
