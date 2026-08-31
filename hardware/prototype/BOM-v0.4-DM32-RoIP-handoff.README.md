# BOM v0.4 — DM-32UV / RoIP handoff, as received

**File:** `BOM-v0.4-DM32-RoIP-handoff.txt`, 1441 lines, received 2026-08-31.

**Status: RECEIVED INPUT, NOT AN ACCEPTED BASELINE.** The document is a draft
baseline-change package for review. It is committed here verbatim so it diffs
and reviews as text, exactly as `prototype-bom-revA.csv` is. Committing it does
not adopt it. Its own header says so: "Requires controlled FML baseline update
before production lock."

Its CONOPS-level companion, the architecture change that would make voice a
baseline capability, is received as `docs/change-requests/CCR-03`. This file
covers the hardware; that one covers the operating concept and the ADR
renumbering both share.

It fits `SAD` section 33.3's purpose for this directory -- what must be
purchased to make the architecture decisions -- and its intent is inside the
CONOPS envelope rather than scope creep: CONOPS section 45 already reserves
external VHF/UHF/HF integration, which this proposes to fill with a specific
radio and an audio/PTT Radio-over-IP gateway.

## What it proposes, in one paragraph

Add the Baofeng DM-32UV as the standard external team voice radio, and give the
MULE an **audio/PTT-level** Radio-over-IP gateway: a dedicated gateway radio's
speaker/mic audio and PTT are carried between MULEs as IP (over Wi-Fi, HaLow,
Ethernet or Tailscale), so two teams on different RF channels can be linked
without the MULE understanding DMR. Direct radio-to-radio operation is preserved
when the MULE is absent. Prototype interface is a DigiRig Mobile (CM108 USB
audio + CP2102 serial RTS PTT). Recurring node target rises to about $763 with a
dedicated gateway radio, or $673 if the radio is group-furnished.

## Blocking issues found on receipt

These are recorded so they are not lost between receipt and review. None is a
reason to reject the direction; the first is a hard identifier conflict that
must be resolved before any of it enters the decision register.

### 1. The three proposed ADR numbers are already taken (hard conflict)

The package proposes `FML-ADR-051`, `FML-ADR-052` and `FML-ADR-053`. **All three
exist and are in force:**

| Number | Already assigned to |
| --- | --- |
| `FML-ADR-051` | node decision logic lives in an importable package |
| `FML-ADR-052` | the boundary between decision functions and blocked services |
| `FML-ADR-053` | **BATMAN-IV is the baseline routing algorithm** |

Identifiers in this repository are permanent and never reused. The routing ADR
in particular is cited across `mule/`, the templates and the benches. **The
voice decisions must be renumbered from the next free block**, allocated with
`tools/new-adr.sh` (the highest in use at receipt was `FML-ADR-063`). The `VOICE-L1-*`
requirement tags and `TBR-VOICE-SW-01` do not collide and are fine, but a `VOICE`
trade area and any ADRs must be allocated with `tools/new-adr.sh` /
`tools/new-trade.sh` rather than hand-numbered, which is how this collision
would have been avoided.

### 2. RoIP over the mesh interacts with three decisions made this week

- **`FML-ADR-063` (per-deployment prefix, overlapping-uplink detection).** A
  voice session is a real-time IP flow across the same bearer whose addressing
  is now per-deployment and whose uplink may silently steal part of the mesh.
  VOICE-L1-003 lists Tailscale and routed WAN as bearers; the route-stealing
  finding applies to them directly.
- **`FML-ADR-061` (keyed mesh, automatic merge).** VOICE-L1-009 requires voice
  authorization distinct from network reachability. That is the same shape as
  the mesh-credential-is-not-admission finding: being on the mesh must not be
  being in the voice group. The BOM states the principle; nothing implements it.
- **QoS (VOICE-L1-012, section 12).** Preferring voice over bulk is new traffic
  policy on a bearer whose behaviour under load is untested. It lands on
  `TBR-RF-01` and the still-unwritten traffic-class work, and it competes with
  the routing daemon that `services/catalog/` warns starves first.

### 3. It adds a service, and the service rules apply

Section 6 requires a "thin MULE RoIP controller" and Status Aggregator fields.
That is a service, and `services/catalog/` is empty by decision: adding one is a
catalog entry and a Quadlet, gated on selection. `TBR-VOICE-SW-01` (thin native
vs SvxLink vs AllStar) is the selection trade and must exist before anything
runs. It also lands on `TBR-COMP-01`, which the package correctly says must be
re-tested with an active RoIP session on the 4 GB CM4.

### 4. The compute claim is plausible, unproven, and the BOM says so

Keeping the 4 GB CM4 with Opus encode/decode plus signaling is reasonable on its
face, and the package does not assert it -- it makes it a `TBR-COMP-01` gate
(VOICE-08) with an explicit fail-condition back to 8 GB. That is the right
posture. The point of exposure is that `TBR-COMP-01` is critical-path, unowned
in practice, and now has one more worst-case contributor.

## What is sound about it

- The audio/PTT gateway choice over native DMR tunnelling is radio-agnostic and
  keeps the MULE out of the RF-protocol business, which matches `docs/NON-GOALS.md`.
- Direct-RF-preserved degradation (VOICE-L1-006, GATE VOICE-05) is exactly the
  local-first / PACE-independence principle the CONOPS requires.
- It proposes gates before baseline lock rather than asserting readiness, and
  its cost section explicitly forbids reading the prototype price as production.
- No frequencies are hard-coded; regulatory configuration is pushed to the
  mission radio plan, consistent with `regions/` and `REGULATORY.md`.

## What review still has to decide, not decided here

Whether RoIP is in scope for MULE v1 at all, or a v-next capability; whether the
gateway service is native or an existing framework; renumbering the ADRs;
opening the `VOICE` trade area; and how voice-group authorization is expressed
against the mesh and Tailscale boundaries. None of that is settled by committing
the document.
