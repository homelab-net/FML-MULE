---
id: FML-ADR-078
title: A node runs only services the catalog approves, and the catalog is machine-checked
status: SELECTED
date: 2026-09-11
supersedes: none
superseded-by: none
trades: [TBR-COMP-01, TBR-TAK-01, TBR-MAP-01]
verification: SIMULATED
---

# FML-ADR-078 A node runs only services the catalog approves, and the catalog is machine-checked

## Context

`services/catalog/README.md` establishes that adding a service to a MULE node is
a recorded decision, not a file appearing in `quadlets/`: a node has one compute
element shared between the network plane and the service plane (`FML-ADR-021`),
so an unbudgeted service starves routing and the node looks like it has a radio
fault when it has a scheduling fault. The mission JSON schema already says every
enabled service "must have an entry in `services/catalog/`" -- and states plainly
that the schema cannot check it and a separate validator will.

Until now there was no such validator, no machine-readable catalog, and the
catalog was empty, so a mission package could enable any service name at all and
nothing objected. That is the gap: a contract asserted in prose and enforced
nowhere.

Two services have been selected for the v0.0.1 direction: OpenTAKServer (the TAK
server) and Martin (the map tile server, `FML-ADR-073`). Their measured resource
envelopes are not settled -- `TBR-COMP-01` and `TBR-MAP-01` remain open -- and
OpenTAKServer publishes no complete official OCI image. The durable-state
boundary is not open: `TBR-TAK-01` closed under `FML-ADR-071`, which decided the
mission-critical TAK state set, so each entry records its durable-state from that
decision rather than deferring it.

## Decision

A node **shall** run only services listed in the service catalog. The catalog is
maintained in machine-readable form (`services/catalog/catalog.yml`) against a
schema (`services/catalog/catalog.schema.json`), and a mission package that
enables a service with no catalog entry **shall** be refused rather than
generating configuration for it. A catalog entry records the fields
`README.md` names; a field blocked on an open trade **shall** carry the string
`TBD` naming that trade, and an entry's image, if given, **shall** be an
immutable digest, never a tag. An entry is a *contract* -- this node may run this
service -- not a claim that its digest or resource envelope is settled.

## Status

SELECTED.

## Consequences

- A committed mission example and a generated node's configuration can enable
  only approved services; `tools/validate-catalog.py` checks the catalog against
  its schema and every mission example against the catalog, and `gen-config`
  refuses an uncatalogued service at generation.
- OpenTAKServer and Martin enter the catalog now, with `TBD` on the fields their
  open trades will supply, so the contract exists before the measurements do.
- What becomes harder: enabling a new service now requires a catalog entry and a
  passing validator, which is the intended friction.
- No effect on the threat model beyond making the exposed-to trust level of each
  service explicit.

## Accepted cost

The catalog entries carry `TBD` for image and resource envelope, so the catalog
approves services whose fielded image and footprint are not yet fixed. Someone
will argue an entry with a `TBD` image is not really "approved to run". It is
approved as a *contract* and gated from deployment by the same trades that gate
everything else; a catalog that admitted only fully-measured services could hold
nothing until `TBR-COMP-01` closes, which would leave the enforcement untestable.

## Fallback

Reversible. The catalog is data and the enforcement is one check plus one guard
in `gen-config`; removing a service is deleting an entry, and reverting the
enforcement is mechanical, at the cost of reopening the "any service name is
accepted" gap.

## Superseded by

None.

## Verification dependency

`tools/validate-catalog.py` (catalog conforms to schema; every mission example's
services resolve to catalog entries) and `test/unit/test_gen_config.py` (an
uncatalogued service is refused; the catalogued services resolve). SIMULATED; the
`TBR-COMP-01` and `TBR-MAP-01` values remain open.
