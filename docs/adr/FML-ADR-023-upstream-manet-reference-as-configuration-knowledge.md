---
id: FML-ADR-023
title: Consume OpenMANET as reference/configuration source, not mandatory production firmware
status: SELECTED
date: 2026-08-25
supersedes: none
superseded-by: none
trades: [TBR-LINUX-01, TBR-RF-01]
verification: Stage 2
---

# FML-ADR-023 Consume OpenMANET as reference/configuration source, not mandatory production firmware

**Source of rationale:** SAD v0.31 section 3.2. See also sections 2.1, 3.5, 4.2,
8.2, 21.2 and 29.

Supersedes the v0.1/v0.2 `AD-003` framing; see SAD section 0.8.

## Context

OpenMANET is an OpenWrt-based open firmware project integrating ATAK multicast
behaviour with supported SBC and HaLow configurations (sources `SR-002`,
`SR-003`). It encodes real configuration knowledge: driver invocation, mesh
parameters, interface bring-up ordering, and known-bad combinations.

The choice was whether to adopt its firmware images as the production baseline
or to treat it as a source of knowledge reimplemented inside this program's own
build and promotion pipeline.

## Decision

The program **shall** consume OpenMANET as an open-source reference
architecture, integration source, configuration baseline and prototype
environment. Its images **shall not** be a mandatory production artifact.

OpenMANET behaviour is preserved or adapted for 802.11s HaLow mesh
configuration, batman-adv/BATMAN-V topology, per-node client addressing,
multicast-oriented ATAK behaviour, mesh-gateway behaviour, Morse Micro
integration patterns, telemetry concepts and field-oriented defaults.

Components **may** be reused directly where portable to the selected Linux host.
OpenWrt/UCI-dependent components **shall not** be automatically ported or
forked; their useful behaviour is first implemented through standard Linux
interfaces where practical.

The MULE team **shall not** create a private OpenMANET fork merely to preserve
firmware-level similarity.

## Status

`SELECTED`.

A prototype **may** run upstream OpenMANET firmware for comparative RF testing,
validating defaults, ATAK multicast characterization, and isolating whether a
failure is MULE-specific or upstream (SAD section 3.5). That does not make it
the production software baseline.

`openmanetd` is likewise permitted as a prototype and reference telemetry source
but production observability does not depend on it (SAD section 21.2), and the
coexistence architecture **shall not** assume it provides deterministic scan or
transmit-suppression primitives (SAD section 8.2, `FML-ADR-027`).

## Consequences

- The program keeps control of its own promotion gate, signing and A/B update
  scheme, which an externally produced image would not have satisfied. See
  `FML-ADR-040` and `FML-ADR-041`.
- The program must reproduce configuration work that already exists, and must
  keep watching upstream for changes it should absorb.
- Divergence from upstream is expected and is not by itself a defect. Where the
  program carries an actual patch rather than re-expressing configuration, that
  is a fork and is registered under `docs/forks/` with a named owner.
- Upstream-first applies: a fix that belongs upstream is offered upstream before
  it is carried here (governing principles 4 and 5, SAD section 0.3).
- The default OpenMANET `10.41.0.0/16` field prefix is retained as the preferred
  initial field prefix, reducing divergence. See `TBR-NET-01`.

## Accepted cost

The program accepts duplicated effort and the risk of drifting from a reference
maintained by people with more sub-GHz mesh experience than this program has. It
accepts that when something does not work, it cannot ask upstream about an image
it does not run.

## Fallback

Adopting upstream images as the production baseline remains possible, at the
cost of the promotion and rollback properties this program has decided it needs.
That would supersede this ADR.

## Superseded by

None.

## Verification dependency

Stage 2. Comparative bring-up against the upstream reference configuration is
the natural evidence. SAD section 30.1 records this as OPEN until a mesh
equivalence test.
