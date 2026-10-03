---
id: TBR-NET-06
title: How does a remote EUD resolve the one service name to its assigned MULE across multiple MULEs
status: OPEN
owner: Cameron Zobrist
area: NET
priority: 99
function-owner: Network
critical-path: false
depends-on: []
feeds: []
requires-hardware: partly
evidence: docs/evidence/TBR-NET-06/
adr: [FML-ADR-031, FML-ADR-082, FML-ADR-086]
target-date: TBD-SRR
---

# TBR-NET-06 How does a remote EUD resolve the one service name to its assigned MULE across multiple MULEs

## Question

When multiple MULEs share the WAN overlay, how does a remote EUD resolve the one stable service
name (`tak.field`) to **its assigned MULE's** ingress, given that Tailscale split-DNS is
tailnet-global (one `field` domain maps to one nameserver for the whole tailnet)?

## Why it matters

`FML-ADR-031` fixes a single stable name (`tak.field`) the EUD never changes; `FML-ADR-082` makes
the assigned MULE the boundary (no silent failover to another MULE); `FML-ADR-086` gives each MULE
a per-MULE overlay identity and leaves the remote ingress a named `TBD`. None of them decides how
the name **resolves** to the assigned MULE over the overlay, and no other trade owns it
(`TBR-NET-01` is the mesh prefix, `TBR-NET-02` is recipient identity, `TBR-NET-05` is the local AP
subnet). The dual AP/tailnet single name has been demonstrated for **one** MULE (see the evidence
directory), using tailnet-global split-DNS -- which cannot route different EUDs to different
assigned MULEs. Until this closes, remote (tailnet) single-name reach works only in a
single-MULE deployment, and the multi-MULE remote-EUD continuity that `FML-ADR-082` enables cannot
be built by name.

## Options

1. **Per-EUD / per-device resolver config** -- each EUD's `.field` resolver points at its assigned
   MULE, pushed at enrollment (a managed profile or QR; the channel roadmap item 4.6 contemplates),
   binding to the `FML-ADR-086` per-MULE identity. Right if per-device config at enrollment is
   acceptable and honors one-name + assigned-only + local-first.
2. **Per-MULE names** (`tak-<mule>.field`) -- right only if the one-stable-name rule
   (`FML-ADR-031`) is relaxed, which would be a CONOPS/ADR change, not this trade.
3. **Tailnet-global split-DNS** (status quo) -- the demonstrated failure; one nameserver cannot
   return a per-EUD answer. Retained only as the single-MULE case.
4. **Central mapping / coordination resolver** -- right only if a central directory were allowed;
   it is not (local-first, no central directory).
5. **MagicDNS per-node names** -- not the stable one-name; breaks `FML-ADR-031`.
6. **Do nothing** -- accept single-MULE-only remote reach. Right only if multi-MULE remote reach is
   out of scope for the increment.

## Closure evidence

Two parts. (a) A written design analysis weighing the options against the four locked constraints
(`docs/evidence/TBR-NET-06/`, already begun). (b) An observation on a **real two-MULE tailnet**
(the two-Pi bring-up): two MULEs each authoritative for `tak.field` to its own overlay address,
and an EUD assigned to MULE-2 that resolves `tak.field` to **MULE-2** (not MULE-1) under the
candidate mechanism, with **no silent failover** to the other MULE when the assigned one is
reachable (`FML-ADR-082`). Real Tailscale, two nodes, one tagged EUD; not netns (netns has no
split-DNS mechanism to exhibit the constraint).

## Closure gate

A comparison. The program agrees the question is answered when the Owner accepts a resolution
mechanism (or an ADR selecting one), **informed by the real two-MULE tailnet observation above**,
that resolves each EUD to **its assigned MULE** while tailnet-global split-DNS demonstrably does
not -- and that honors all four constraints: one stable name (`FML-ADR-031`), assigned-MULE-only
with no failover (`FML-ADR-082`), the per-MULE identity with the ingress left to its owner
(`FML-ADR-086` / PBCR-01), and local-first with no central directory. This gate does **not** close
on the written analysis alone.

## Dependencies

- **Depends on:** none to begin the analysis; the closure observation depends on a real two-MULE
  tailnet (the two-Pi hardware bring-up).
- **Feeds:** the remote-EUD single-name implementation; the `PBCR-01` field-service-plane ingress
  definition; any future remote extension of `FML-ADR-031`.
- **Related decisions:** `FML-ADR-031`, `FML-ADR-082`, `FML-ADR-086`; roadmap item 4.6
  (enrollment/onboarding channel) and `PBCR-01` (ingress definition) are named dependencies, not
  assumed solved.
- **Validating stage:** Stage 6 (WAN overlay).
- **Requires hardware:** partly -- the analysis is hardware-free; the closure observation needs a
  real two-MULE tailnet.
