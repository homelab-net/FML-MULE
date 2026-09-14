# Partition and rejoin: reconciling time across a mesh merge

**Trade:** `TBR-TIME-01`.
**Date:** 2026-09-14.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** analysis. No bench and no hardware; this is the
"partition rule" the trade names as workable without either (see the trade's
**Requires hardware** note). It reasons toward a rule and options; it decides
nothing, and closes nothing.

## Why this exists

`FML-ADR-061` makes MULEs of one deployment **merge automatically** when they
meet, and records that this "makes the addressing collision the normal case
rather than the exceptional one" -- `FML-ADR-063` handles the addressing half.
There is a second thing two nodes carry into a merge: **their clocks.** Each may
have been on holdover for hours, drifting, since it last saw a trusted source.
`FML-ADR-042` decides how a *single* node judges its own retained time
(`mule/timekeeping.py:assess` -- synced short-circuits to `CREDIBLE`, otherwise
the retained-time checks run, and any doubt is `TIME_DEGRADED`, fail closed). It
does **not** decide what happens when two nodes' clocks meet on a merged mesh.
That gap is this note's subject, and it is the "partition-rejoin reconciliation"
`TBR-TIME-01` lists as its harder, hardware-free half.

## What `assess` already gives, and where it stops

`assess` is per-node and already fail-closed: a node that cannot trust its own
clock refuses admission and will not fail a certificate check open. What it does
not model is a **distribution** question -- whether, and how, a node may take
time *from a peer* it just merged with. Nothing in `mule/` adopts a peer's time
today, so the current behaviour on merge is simply that each node keeps judging
by its own clock, and any node whose holdover has drifted past the (still `TBD`)
skew window is `TIME_DEGRADED` until a trusted source returns. That is safe. It
is also the most conservative option, and the trade should decide whether it is
the intended one.

## The principle the rule must hold

**Being on the merged mesh is not being a trusted time source.** This is the
same shape as `FML-ADR-061`'s own admission finding (holding the mesh credential
admits a node to the *network*, "there is no compartmentation below that") and
the same shape as the voice-group-across-merge question recorded in
`docs/architecture/roip-voice-data-flow.md`: network reachability is not
authorization for a specific trust. A peer that can route to me is not thereby
allowed to move my clock, because time underwrites certificate validity
(`FML-ADR-042`, `FML-ADR-036`), and a clock an adversary can push is a
certificate window an adversary can forge. `FML-ADR-042`'s own hierarchy already
ranks a peer **last** (GNSS/NTP, then chrony, then local, then peer), and never
as a sole source.

## Four cases at the moment of merge

| Node A | Node B | What must happen |
| --- | --- | --- |
| `CREDIBLE` (synced) | `CREDIBLE` (synced) | Both trust their own clocks; nothing to reconcile. Small skew between two synced clocks is within the trusted-source tolerance. |
| `CREDIBLE` | `DEGRADED` (holdover) | B may only discipline toward A if A can be **authenticated as a trusted time source** -- a trust distinct from mesh admission, which does not exist yet (`TBR-SEC-01`, `TBR-ID-01`). Absent that, B stays `DEGRADED` and fails closed. |
| `DEGRADED` | `DEGRADED` | Neither is a source of truth. Neither adopts the other. Both stay `DEGRADED`; certificates judged across the merge do not fail open (`FML-ADR-042`). |
| any | hostile / faulty | A captured or dead-RTC node must not be able to push time onto the mesh. Any peer-suggested time is bounded by the skew window and gated by the (missing) time-source authentication; an unauthenticated or out-of-window suggestion is rejected, not adopted. |

## The rule this points to (shape decided, values open)

1. **Never above the hierarchy.** A peer's time is used only when no
   higher-ranked source (GNSS/NTP, chrony, local retained-and-credible) is
   available -- `FML-ADR-042`'s order, unchanged.
2. **A peer is a time source only if authenticated as one**, by a credential
   distinct from the mesh credential. That credential's distribution is the gap
   `TBR-SEC-01` records; until it exists, peer time cannot be safely adopted at
   all.
3. **Bounded by the skew window.** Even an authenticated peer cannot move the
   clock backward, or forward past `max_plausible_forward`, beyond the tolerances
   `TimePolicy` carries as `TBD` (`TBR-TIME-01`). The values are the trade's; the
   bound's existence is not optional.
4. **Unresolved divergence fails closed**, exactly as a single node's doubt does
   today.

## Options for the trade

- **A -- no peer time distribution in v1.** Nodes use GNSS/NTP/chrony/local
  only; peers never set each other's clocks. On merge, each keeps its own
  assessment; drifted nodes are `TIME_DEGRADED` until a trusted source returns.
  Simplest, most conservative, and buildable now because it needs no new
  credential. It is also what the code does today by omission.
- **B -- authenticated peer time as a last resort.** A node may discipline to a
  peer authenticated as a trusted time source, within the skew window. Strictly
  more capable, and strictly blocked on the time-source credential
  (`TBR-SEC-01`, `TBR-ID-01`).
- **C -- between the two**, e.g. peer time accepted only to *raise suspicion*
  (force a re-sync attempt) but never to set the clock.

**Direction, not a decision:** v1 leans to option A. The credential that would
make option B safe does not exist (`TBR-SEC-01`), and adopting peer time on mesh
admission alone would violate the principle above. Option A keeps the fail-closed
posture `FML-ADR-042` already holds, and loses only opportunistic re-sync that no
part of the program yet depends on. The trade owner decides.

## What this is not

- **Not a closure of `TBR-TIME-01`.** It is the hardware-free half; drift and
  holdover values still need candidate-RTC measurement, and the rule's
  thresholds are the trade's to set.
- **Not an implementation.** No reconciliation code is added; `assess` stays
  per-node. Option B in particular cannot be implemented until `TBR-SEC-01`
  provides the credential.
- **Not a new ADR.** It reasons within `FML-ADR-042`'s decided rule; if the trade
  selects option B, that is a new decision to record then.

## Cross-references

- `docs/adr/FML-ADR-042-retained-local-time-fail-closed.md` -- the per-node rule
  and the source hierarchy this extends to the merge case.
- `docs/adr/FML-ADR-061-the-mesh-is-keyed-and-mules-of-one-deployment-merge-automatically.md`
  -- automatic merge, and the admission-is-not-compartmentation shape reused here.
- `docs/adr/FML-ADR-063-per-deployment-ipv4-prefix-and-overlapping-uplink-detection.md`
  -- the addressing half of the same "merge is the normal case" hazard.
- `docs/trades/TBR-SEC-01-protected-storage-unlock.md`,
  `docs/trades/TBR-ID-01-browser-service-identity-provider.md` -- the missing
  credential that gates option B.
- `mule/timekeeping.py`, `docs/readings.md` (Time) -- the per-node assessment and
  its readings.
- `docs/architecture/roip-voice-data-flow.md` -- the voice-group-across-merge
  question, the same principle applied to a different trust.

Nothing real: no deployment location, member identity, callsign, credential, or
operational capture. See `SECURITY.md`.
