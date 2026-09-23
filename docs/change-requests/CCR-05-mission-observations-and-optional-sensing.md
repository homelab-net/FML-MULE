# CCR-05 Mission observations and optional sensing

**Type:** CONOPS change request
**Status:** `OPEN`
**Target version:** CONOPS **v1.2**, if accepted. v1.1 is not edited by this draft.
**Sections affected:** 49, 50.12, 78 Stage 1, 79, 85
**Raised by:** the 2026-09-23 enhancement direction, for the part not already controlling
**Decision:** none. This request does not open an ADR.

## Statement

`CCR-04` and `FML-ADR-082` already made the remote-EUD overlay baseline. This
request drafts the rest of that direction which is still only an engineering
handoff: how a mission observation ages, what an optional sensor is allowed to
break, and what a derived report is not allowed to claim.

It is not accepted. It has no weight. It does not reissue the CONOPS, does not
enlarge `v0.0.1`, and does not change `mule/`, the mission schema, or section
50's mode list. `CCR-01` and `CCR-03` stay open and are not folded in.

## Already controlling, and not redrafted here

These stay as they are. This request does not add a second copy.

| Subject | Where it already is |
| --- | --- |
| Local operation survives loss of WAN | CONOPS section 1 |
| Reachability is not authorization | CONOPS sections 1 and 13 |
| Unit Member, Team Lead, alternate | CONOPS section 7; `FML-ADR-037` |
| TAK authority, including stale shared TAK state | CONOPS sections 26 through 29 |
| Overlay posture, assigned ingress, one mission-and-team tag | CONOPS v1.1 sections 12 and 43; `FML-ADR-082` |
| Access-point passthrough is not overlay membership | `FML-ADR-068` |
| Prefer an existing representation; no rich document on a constrained link | `FML-ADR-048` |
| No new awareness process until a boundary is earned | `FML-ADR-051`, `FML-ADR-052` |
| EMCON entry, indication, override, and re-entry | CONOPS section 50.12 |
| No interception, persistent tracking, raw IQ, or emitter fix | `docs/NON-GOALS.md`, CONOPS section 81 |

`CORE_READY` and `PENDING_WAN` are not given names here. The WAN half of that
behavior is already a v1.1 `[SHALL]`. The sensor half is the new sentence
below, and it does not invent a status word.

## 1. Sections affected

- Section 49, which names approved sensors and has no `[SHALL]`.
- Section 50.12, whose only `[SHALL]` is the entry procedure. The
  receive-dominant sentence under it is prose.
- A new section, placed after section 28 and numbered at reissue. Section 28
  is not rewritten. TAK authority and a mission observation are different
  things.
- Section 78 Stage 1, by adding bullets. No new stage.
- Section 79, by adding criteria. Section 85 gains one row per new criterion,
  each pointing at Stage 1.

## 2. Current text

Section 49 lists approved sensors and approved AI/RAG as browser applications.
It then says exact products are downstream selections. It binds nothing about
a sensor failing, a person tasking one, or a product being derived.

Section 50.12 describes receive-dominant operation "where technically
feasible." It does not say that this is a claim of measured silence, and it
does not say reception continues.

No section defines a mission observation, its age, a queue, a link report, or
a summary.

## 3. Proposed text

The words below are the proposed `[SHALL]` text. They are not in the CONOPS
until this request is accepted and v1.2 is issued.

### Mission observations

Placed after section 28. Section 28's four TAK conditions stay the words for
shared TAK authority. They are not reused for a sensor report.

[SHALL] A mission observation shall record the time it was observed, the
source that produced it, and whether it is new, active, stale, expired,
merged, or superseded.

[SHALL] A stale or expired observation shall not be presented as current.

[SHALL] Relaying, queuing, or later delivery shall not replace the time of
observation with the time of delivery.

[SHALL] An expired observation shall remain history for the retention the
mission profile sets. Expiry shall not be treated as deletion.

[SHALL] An observation of one subject shall not be merged with an observation
of a different subject. A possible match shall not be presented as a confirmed
identity.

[SHALL] A report that a link was heard shall not be presented as proof that
the path can carry traffic, and shall not be presented as the location of an
emitter.

[SHALL] A summary, alert, or other derived product shall identify the
observations it came from and shall not replace those observations. A product
of a model shall be labeled as a model product and shall not be presented as
an observation.

[SHALL] While the node cannot deliver, locally produced observations shall
still be kept, up to a bound set by the mission profile. Discarding one to
stay inside that bound shall be recorded. The bound shall not by itself end
local participation.

### Optional sensing

Added to section 49.

[SHALL] A mission profile shall be able to mark a capability required,
optional, or off.

[SHALL] A capability marked off shall not be tasked.

[SHALL] Refusal, failure, or absence of an optional capability shall not by
itself make local mission participation unsuccessful.

[SHALL] A capability the mission profile marks required, and that is absent,
shall be shown as missing. It shall not be shown as available.

[SHALL] Authority to view a mission product shall not by itself be authority
to task a sensor, and neither shall by itself be authority to administer a
node.

[SHALL] Authority to task a sensor shall name the sensor, the duration, and
the team scope. A task shall end when that duration ends, an authorized
person stops it, or it completes. Its result shall be an observation or a
recorded failure.

[SHALL] A change of permission on a capability shall be recorded.

These sentences do not add the role names view, task, and administer. Section
7's Unit Member, Team Lead, and alternate remain the roles. `FML-ADR-037`
remains the rule for how role and scope are enforced.

### EMCON collection

Added to section 50.12, after the existing entry-procedure `[SHALL]`. No new
mode is named. `CCR-01` still owns whether the section 50 modes are
concurrent and what their transitions are. This request does not close it.

[SHALL] While EMCON is in effect, the system shall not originate a
transmission the active posture has classed as avoidable.

[SHALL] EMCON shall not be reported as measured radio silence. Measured
silence is a measurement, not a mode.

[SHALL] Where the active posture still permits reception, a prohibition on
transmission shall not by itself be reported as an inability to receive.

## 4. What this request deliberately does not say

- It does not admit interception, traffic analysis, persistent tracking, raw
  IQ recording, or an emitter location. Those stay in section 81.
- It does not choose a store, a schema, a wire encoding, a process, a tag
  spelling, or an ACL. Those are not operational obligations, and the ones
  that are already decided stay in the ADRs named above.
- It does not make scenarios, screen layouts, or example sensor lists into
  requirements.
- It does not move `CCR-03`'s voice baseline. That request is still open and
  still names v1.1, which has since been issued for a different change.

## 5. Operational rationale

A person who can see a stale sensor report and believe it is current will act
on it. A sensor the mission did not require must not be able to fail the rest
of the local mission. A summary that hides its sources cannot be checked when
the node is disconnected, which is the normal case.

The engineering handoff described those behaviors. Leaving them only in that
file means they are not obligations. Putting them in v1.2 makes them
obligations. Until this request is accepted, they remain the handoff.

## 6. Downstream documents, if accepted

Not edited by this draft.

| Document | What acceptance would change |
| --- | --- |
| CONOPS | Reissue as v1.2. v1.1 stays the historical copy. |
| Section 79 and section 85 | Four criteria, all allocated to Stage 1. |
| Section 78 Stage 1 | The same four behaviors as stage bullets. |
| SAD | Transcribe the new section. No new decision in section 0.8. |
| `docs/verification/requirements.md` | New requirement rows, traced to Stage 1. |
| `docs/NON-GOALS.md` | No removal. |
| `mule/`, mission schema, `FML-ADR-082` | No change. |

The four proposed criteria are:

1. A stale or expired mission observation is not presented as current.
2. Refusal or absence of an optional capability does not by itself fail local
   participation.
3. A link report is not presented as an emitter location or as proof of a
   usable path.
4. A derived product identifies its source observations and does not replace
   them.

## 7. Verification impact

Section 85 already requires every section 79 criterion to name a stage. The
proposed rows name Stage 1. No stage is added. Nothing in this request has
been run. Acceptance would not make any of it `SIMULATED` or
`HARDWARE-VERIFIED`.

## 8. Approval

Not approved. Status remains `OPEN`.
