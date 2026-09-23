# CCR-05 Mission observations and optional sensing

**Type:** CONOPS change request
**Status:** `OPEN`
**Target version:** CONOPS **v1.2**, if accepted. v1.1 is not edited by this draft.
**Sections affected:** 49, 50.12, 78 Stages 1, 9 and 10, 79, 81, 85
**Raised by:** the 2026-09-23 enhancement direction, for the part not already controlling
**Decision:** none. This request does not open an ADR.

## Statement

`CCR-04` and `FML-ADR-082` already made the remote-EUD overlay baseline. This
request drafts the rest of that direction which is still only an engineering
handoff: how a mission observation ages, what an optional sensor is allowed to
break, and what a derived report is not allowed to claim.

It is not accepted. It has no weight. It does not reissue the CONOPS, does not
enlarge `v0.0.1`, and does not change `mule/`, the mission schema, or section
50's mode list. `CCR-01` stays open. `CCR-03` is `APPROVED` and is not folded
into this draft. Its voice text was not in the v1.1 issue. A later v1.2
reissue that accepts this request must also carry that already-approved voice
text. This request does not draft it.

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
- Section 81, by proposing exclusions that are not in v1.1. `docs/NON-GOALS.md`
  is not edited until acceptance, because it transcribes section 81.
- Section 78 Stages 1, 9, and 10, by adding bullets. No new stage.
- Section 79, by adding one criterion per new `[SHALL]` below. Section 85
  gains one row per criterion. The stage is the one named in section 7, not
  Stage 1 for all of them.

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

### Sensing that v1 does not require

Added to section 81. These are not in v1.1 and they are not in
`docs/NON-GOALS.md`. They are proposed here so acceptance would make them
exclusions. Until then they are not prohibitions.

MULE v1 shall not require, and shall not include as a baseline capability:

- interception of communications content not addressed to the mission;
- persistent tracking of a third party who is not a mission participant;
- collection of raw IQ;
- an emitter location derived from a link report;
- collection of credentials from an observed network;
- collection of a cellular identity, including an IMSI.

Section 57 already tells a member that participation may include the team's
own location tracking. That notice is not this exclusion, and this exclusion
does not remove it.

## 4. What this request deliberately does not say

- It does not choose a store, a schema, a wire encoding, a process, a tag
  spelling, or an ACL. Those are not operational obligations, and the ones
  that are already decided stay in the ADRs named above.
- It does not make scenarios, screen layouts, onboarding screens, an iOS
  distribution check, or example sensor lists into requirements. Those remain
  in the engineering handoff.
- It does not draft `CCR-03`. That request is `APPROVED`. Its voice text was
  not in the v1.1 issue. A v1.2 reissue that accepts this request must carry
  that text as well. This file does not contain it.

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
| CONOPS | Reissue as v1.2, and carry the already-approved `CCR-03` voice text in that same reissue. v1.1 stays the historical copy. |
| Section 79 and section 85 | One criterion per `[SHALL]` in section 3, allocated as section 7 says. |
| Section 78 | Bullets on Stages 1, 9, and 10 for those same behaviors. No new stage. |
| Section 81 | The six sensing exclusions in section 3. Not section 79 criteria. |
| SAD | Transcribe the new section. No new decision in section 0.8. |
| `docs/verification/requirements.md` | New requirement rows, traced to the stage in section 7. |
| `docs/NON-GOALS.md` | Transcribe the new section 81 exclusions. No removal. |
| `mule/`, mission schema, `FML-ADR-082` | No change. |

## 7. Verification impact

Every new `[SHALL]` has a stage and a method. Nothing here has been run.
Acceptance would not make any of it `SIMULATED` or `HARDWARE-VERIFIED`.
The EMCON rows are a flat-sat of what the node reports and sends. They are
not a measurement of radio silence.

| `[SHALL]` | Stage | Method |
| --- | --- | --- |
| Observation records time, source, and state | 1 | Demonstration: a flat-sat observation carries all three, and the state is one of the six named words. |
| Stale or expired is not presented as current | 1 | Demonstration: a stale and an expired observation are shown as such. |
| Relay or queue does not replace the observation time | 1 | Demonstration: deliver a queued observation and compare the two times. |
| Expiry retains history for the profile's retention | 1 | Demonstration: an expired observation is still retrievable, and a retention bound discards only past that bound. |
| Different subjects are not merged; a possible match is not an identity | 1 | Demonstration: two subjects stay two records, and a candidate match is labeled as a candidate. |
| A link report is not a usable path and not an emitter location | 1 | Inspection of the presented report. No geolocation claim is produced. |
| A derived product names its sources and does not replace them; a model product is labeled | 1 | Demonstration: remove the product and the sources remain; a model product is marked as one. |
| A full queue records the discard and does not end local participation | 1 | Demonstration: fill the bound, observe the recorded discard, and confirm local service still answers. |
| A profile can mark a capability required, optional, or off | 1 | Demonstration against a mission-profile fixture. The schema field is not this test. |
| A capability marked off is not tasked | 1 | Demonstration: a task against an off capability is refused. |
| Optional refusal, failure, or absence does not fail local participation | 1 | Demonstration: deny the optional capability and complete local participation. |
| A required capability that is absent is shown as missing | 1 | Demonstration: the status says missing, not available. |
| View is not task, and neither is node administration | 9 | Demonstration: a view-only principal is refused a task and an administration action. |
| A task names sensor, duration, and team scope, ends on those conditions, and yields an observation or a recorded failure | 9 | Demonstration: expire the duration, stop it, and complete it. Each end is recorded. |
| A permission change is recorded | 9 | Inspection: the change is in the administrative record. |
| EMCON does not originate an avoidable transmission | 10 | Demonstration on a flat-sat: the classed transmission is absent. Not an RF measurement. |
| EMCON is not reported as measured radio silence | 10 | Inspection: the reported state does not say measured silence. |
| A transmit prohibition is not reported as an inability to receive, where reception is still permitted | 10 | Demonstration: the reported receive state stays permitted. |

The six section 81 exclusions are scope. They follow the existing section 81
list, which is not a set of section 79 criteria. Acceptance checks them by
inspection of the reissued section 81 and of `docs/NON-GOALS.md`.

## 8. Approval

Not approved. Status remains `OPEN`.
