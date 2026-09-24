---
id: FML-ADR-080
title: Per-peer link capability is a named tier derived from passive signals
status: SELECTED PRINCIPLE
date: 2026-09-18
supersedes: none
superseded-by: none
trades: [TBR-RF-01]
verification: TBD
---

# FML-ADR-080 Per-peer link capability is a named tier derived from passive signals

## Context

The operator view (`docs/ROADMAP-DEV.md` item 4.7, CONOPS section 67) is
capability-first: it answers what a link can carry to a given peer -- video,
voice, or only text -- rather than making an operator read routing tables. Item
1.9's passive floor is meant to derive that answer from signals the node already
has: batman-adv transmit quality (TQ), the `iw station dump` PHY-rate ceiling,
the bearer, and the hop count. The parser for those signals now exists
(`test/digital_twin/radio_parse.py`: `station_bitrates_mbps` and `originator_tqs`).

What does not exist is a name for the answer. The only capability ladder the
program has is node-level and describes graceful degradation of the whole node,
not a single link: `mule/modes.py`'s `BearerCapability`
(`NOMINAL-IP`/`DEGRADED-IP`/`LOW-BANDWIDTH`/`ISOLATED`), transcribed from CONOPS
section 50 by `CCR-01`. No controlling document names what a *per-peer link* can
carry.

That gap is not cosmetic. `FML-ADR-052` condition 2 forbids a `mule/` decision
function from inventing vocabulary: every state name it produces must be
transcribed from a controlling document or supplied by the caller. So a per-peer
capability function cannot be written until a document names its tiers. Doing
nothing leaves item 4.7's capability-first view unimplementable and item 1.9's
passive floor without an output to name. This ADR is that document.

## Decision

Per-peer link capability **shall** be reported as one of a named, ordered set of
tiers, defined here as the per-link view of the CONOPS section 50 degradation
ladder and grounded in the application each tier carries:

- `VIDEO` -- the link can carry peer video over the high-rate mesh
  (`FML-ADR-025`); the per-link view of `NOMINAL-IP`.
- `VOICE` -- the link can carry audio and PTT over IP (`FML-ADR-065`, `CCR-03`)
  but not video; the per-link view of `DEGRADED-IP`.
- `TEXT` -- the link can carry TAK chat and position, the capability of the LoRa
  text plane (`FML-ADR-026`); the per-link view of `LOW-BANDWIDTH`.
- `NONE` -- no usable link to the peer; the per-link view of `ISOLATED`.
- `UNKNOWN` -- the available signals cannot tell. `UNKNOWN` is not `NONE`, the
  same distinction `mule/addressing.py`'s `Outcome` draws between `UNKNOWN` and
  `CLEAR`, and the form `FML-ADR-052` condition 3 requires for anything a
  blocking trade would decide.

The passive derivation **shall** only rule a tier *out* or report it as a
ceiling; it **shall not** assert that a tier is achievable end to end. Passive
signals -- TQ, the PHY-rate ceiling, the bearer and the hop count -- are an upper
bound and a loss estimate, not a measured goodput (`FML-ADR-053`). Item 1.9's
paced active probe is what confirms a tier *in*.

The threshold values that map a signal to a tier -- the Mb/s and TQ cut points --
**shall not** be set in this ADR. They belong to `TBR-RF-01` and **shall** be
supplied to any implementation as caller policy, with no compiled-in defaults,
the discipline `mule/timekeeping.py` already applies to `TimePolicy`. This ADR
names the tiers and the rules; it does not name the numbers.

## Status

`SELECTED PRINCIPLE`.

Decided: the tier vocabulary, its correspondence to the CONOPS section 50 ladder,
the rule-out-not-confirm discipline, and that thresholds are caller policy owned
by `TBR-RF-01`. Left to a later implementation ADR and to `TBR-RF-01`: the
threshold values, and the pure `mule/capability.py` function that transcribes
these tiers under `FML-ADR-052` -- taking the signals as plain arguments, its
reading Protocol staying in `test/` per condition 4.

## Consequences

- A per-peer capability function becomes buildable: `mule/capability.py` can
  transcribe these tier names from a controlling document rather than inventing
  them, satisfying `FML-ADR-052` condition 2.
- Item 4.7's capability-first view and item 1.9's passive floor gain a named
  output to produce and display.
- `TBR-RF-01` inherits an obligation it did not have: to set the tier
  thresholds, alongside the QoS mechanism it already owns.
- The report stays honest by construction: a passive tier is a ceiling, so the
  view presents it as "cannot exceed", not "will carry". Anything stronger waits
  on the probe and on hardware.
- A contributor without hardware can implement and test the function against
  fixtures; what they cannot do is claim the thresholds are right, which is the
  hardware half.

## Accepted cost

The program accepts a second capability taxonomy to keep coherent with the first.
`VIDEO`/`VOICE`/`TEXT`/`NONE` is a new set of names beside CONOPS section 50's
`NOMINAL-IP`/`DEGRADED-IP`/`LOW-BANDWIDTH`/`ISOLATED`, and two ladders that drift
apart would be worse than one. The cost is bounded by defining the new tiers *as*
the per-link view of the existing ladder rather than as a competitor, so the
correspondence above is a maintenance obligation, not a coincidence.

The tiers are `UNVERIFIED` design intent. Whether four rungs are the right cut of
the capability space, and where their thresholds fall, is unmeasured until
`TBR-RF-01`; this ADR could be found to have too many rungs, or too few.

## Fallback

Report the raw per-peer signals -- TQ, the PHY-rate ceiling, the hop count --
without a named tier, and let the operator read them. That needs no taxonomy and
no `mule/` function, and it is a strictly weaker operator view (numbers, not
outcomes). The signal to take it is evidence that the tiers cannot be mapped
stably from the passive signals, or that `TBR-RF-01` cannot set thresholds that
mean the same thing across bearers and hardware.

## Superseded by

None.

## Verification dependency

`TBD`, owned by `TBR-RF-01`. The thresholds and the accuracy of the mapping are
hardware-measurable -- the passive floor rules a tier out, and the paced probe of
item 1.9 confirms it in, both on real radios. Nothing here is measured; the
parser this builds on is `SIMULATED` against `mac80211_hwsim` fixtures.
