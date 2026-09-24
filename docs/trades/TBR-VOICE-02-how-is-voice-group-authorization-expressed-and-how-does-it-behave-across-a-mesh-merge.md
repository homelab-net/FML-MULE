---
id: TBR-VOICE-02
title: How is voice-group authorization expressed and how does it behave across a mesh merge
status: OPEN
owner: Cameron Zobrist
area: VOICE
priority: 99
function-owner: Network
critical-path: false
depends-on: [TBR-SEC-01, TBR-VOICE-01]
feeds: []
requires-hardware: no
evidence: docs/evidence/TBR-VOICE-02/
adr: [FML-ADR-061, FML-ADR-067]
target-date: 2026-09-30
---

# TBR-VOICE-02 How is voice-group authorization expressed and how does it behave across a mesh merge

**Source:** `docs/change-requests/CCR-03-integrated-rf-dm32-roip-voice.md` and
`docs/architecture/roip-voice-data-flow.md`, which raise this as an open
question. CONOPS sections 43, 44 (reachability versus membership) and 45
(external RF integration).

## Question

By what credential is voice-group membership expressed -- distinct from being
reachable on the mesh -- and what happens to that membership when `FML-ADR-061`
merges two deployments' meshes automatically?

## Why it matters

`FML-ADR-067` states a single active egress per voice group per local net, and
`CCR-03` adds a `[SHALL]` that voice-group authorization is distinct from network
reachability. `docs/architecture/roip-voice-data-flow.md` shows why: the RoIP
gateway's loop and double-copy prevention rests on knowing which nets form one
voice group, and its refusal to bridge a net to itself rests on voice group not
equalling reachability. **Nothing implements any of it.** There is no
representation of a voice group in the codebase, no membership credential, and no
gateway service to enforce a boundary.

Two decided things make this urgent rather than theoretical. `FML-ADR-061` makes
same-credential meshes **merge automatically** -- so if voice-group membership
were derived from mesh membership, two deployments that meet would merge their
voice groups with no operator action, which is exactly what must not happen. And
the credential that would express membership separately has the distribution and
rotation gap `TBR-SEC-01` records ("`fleet rekey` ... has no mechanism"): there
is nowhere for a voice-group credential to come from. Until this is answered,
`TBR-VOICE-01` cannot build a gateway that enforces group boundaries, and the
`FML-ADR-067` invariant is a principle with nothing behind it.

This is the same shape as two findings already recorded: being on the keyed mesh
is not admission below the network layer (`FML-ADR-061`), and a merged mesh must
not merge two nodes' notion of trusted time
(`docs/evidence/TBR-TIME-01/2026-09-14-partition-rejoin-time-reconciliation.md`).
Reachability is not authorization for a specific trust.

## Options

1. **Voice group derived from mesh membership.** Simplest, and wrong: it merges
   voice groups whenever the meshes merge, violating the `CCR-03` `[SHALL]`, and
   a cross-organization partner on a routed liaison (`TBR-NET-03`) would be
   inside the voice group by reachability. The right answer only if the program
   decides a deployment is always exactly one voice group and never links to
   another -- which contradicts the linking the capability exists for.
2. **A separate voice-group credential**, distinct from the mesh credential,
   distributed by whatever `TBR-SEC-01` settles for credentials. Membership is an
   explicit act, not a side effect of routing; on merge, groups stay separate
   unless deliberately joined. The right answer if voice groups must be finer- or
   coarser-grained than deployments, which cross-team linking implies. Blocked on
   `TBR-SEC-01` for the credential and on `TBR-VOICE-01` for the gateway that
   reads it.
3. **Defer beyond a single configured group in v1.** A MULE bridges only within
   one configured voice group per local net; cross-net and cross-deployment voice
   are out of scope for v1, consistent with `TBR-NET-03` shipping no
   cross-organization mesh mechanism in v1. The right answer if the credential
   work cannot land in the v1 window; it keeps the `FML-ADR-067` invariant
   trivially (one group) without inventing a credential that does not exist.

**Direction, not a decision:** v1 points at option 3 -- one configured voice
group, no automatic cross-merge -- because option 2's credential is the
`TBR-SEC-01` gap and option 1 is unsafe. Option 2 is the path once the credential
exists. The trade owner decides.

## Closure evidence

A design that specifies how voice-group membership is represented and
authorized, naming the credential and where it comes from (via `TBR-SEC-01`), and
a bench demonstration -- once the RoIP gateway (`TBR-VOICE-01`) and the
credential exist -- that two deployments whose meshes merge automatically
(`FML-ADR-061`) keep **separate** voice groups, with `FML-ADR-067`'s single
active egress per group per local net holding across the merge, and no cross-group
audio path formed.

Evidence is committed under `docs/evidence/TBR-VOICE-02/`.

## Closure gate

The program agrees the question is answered when voice-group membership is
expressed by a credential distinct from mesh admission, its distribution is
defined, and a bench shows two merged meshes retaining separate voice groups with
the single-egress invariant intact. The comparison is against `FML-ADR-067`: a
configuration that can place two copies in one ear, or that merges voice groups
because the networks merged, fails the gate.

## Dependencies

- **Depends on:** `TBR-SEC-01` (the credential's distribution and rotation),
  `TBR-VOICE-01` (the gateway that would read and enforce membership).
- **Feeds:** none yet; it constrains the `TBR-VOICE-01` gateway design.
- **Related decisions:** `FML-ADR-061` (automatic merge), `FML-ADR-067`
  (single audio egress), `FML-ADR-070` (carrying a recipient in upstream's own
  fields, the precedent for expressing membership without a custom tag).
- **Validating stage:** `TBD`. The CONOPS text is issued in v1.2 under
  `CCR-03`. The mesh-merge case is not a section 79 criterion yet.
- **Requires hardware:** no. The design and the merge behaviour are exercisable
  on the mesh bench once the gateway and credential exist; neither needs a radio.
